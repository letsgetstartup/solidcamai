from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, List
from datetime import datetime, timezone

import httpx

from .base import ErpConnector, ErpEntitySpec
from .registry import register

@dataclass
class SapB1ServiceLayerConfig:
    base_url: str            # e.g. https://sapb1.company.com:50000
    company_db: str
    username: str
    password: str
    verify_tls: bool = True
    timeout_s: float = 30.0

@register("sap_b1_service_layer")
class SapB1ServiceLayerConnector(ErpConnector):
    """
    SAP Business One Service Layer connector (HTTP/OData).

    Implementation notes:
    - Uses session cookies from /Login
    - Uses OData paging ($top, $skip)
    - Incremental sync via updated_at_field when available (configurable)
    """

    def __init__(self, cfg: SapB1ServiceLayerConfig, entity_catalog: Optional[List[ErpEntitySpec]] = None):
        self.cfg = cfg
        self._client = httpx.AsyncClient(
            base_url=self.cfg.base_url.rstrip("/"),
            verify=self.cfg.verify_tls,
            timeout=self.cfg.timeout_s,
        )
        self._session_cookies: Dict[str, str] = {}
        self._entities = entity_catalog or [
            # These endpoint names are common in Service Layer deployments,
            # but can differ by version/customization; keep configurable via catalog.
            ErpEntitySpec(name="items", endpoint="Items", primary_key_field="ItemCode", updated_at_field="UpdateDate"),
            ErpEntitySpec(name="business_partners", endpoint="BusinessPartners", primary_key_field="CardCode", updated_at_field="UpdateDate"),
            ErpEntitySpec(name="sales_orders", endpoint="Orders", primary_key_field="DocEntry", updated_at_field="UpdateDate"),
            ErpEntitySpec(name="production_orders", endpoint="ProductionOrders", primary_key_field="DocEntry", updated_at_field="UpdateDate"),
        ]

    async def _login(self) -> None:
        url = "/b1s/v1/Login"
        payload = {
            "CompanyDB": self.cfg.company_db,
            "UserName": self.cfg.username,
            "Password": self.cfg.password,
        }
        r = await self._client.post(url, json=payload)
        r.raise_for_status()

        # Persist cookies (B1SESSION / ROUTEID etc.)
        self._session_cookies = dict(r.cookies)
        if not self._session_cookies:
            # Some environments still set cookies; if not, auth might be tokenized differently.
            # Keep as warning; future extension can add token auth if needed.
            pass

    async def _ensure_session(self) -> None:
        if not self._session_cookies:
            await self._login()

    async def healthcheck(self) -> Dict[str, Any]:
        await self._ensure_session()
        # simplest: call a small endpoint; /CompanyService can exist but not always.
        # We'll call /b1s/v1/$metadata as lightweight sanity check.
        r = await self._client.get("/b1s/v1/$metadata", cookies=self._session_cookies)
        ok = (200 <= r.status_code < 300)
        return {"ok": ok, "status_code": r.status_code}

    def list_entities(self) -> List[ErpEntitySpec]:
        return self._entities

    def _build_odata_query(self, entity: ErpEntitySpec, since: Optional[datetime], top: int, skip: int) -> str:
        params = []
        params.append(f"$top={top}")
        params.append(f"$skip={skip}")

        if entity.select:
            params.append("$select=" + ",".join(entity.select))

        filters = []
        if since and entity.updated_at_field:
            # Many SAP B1 deployments expose UpdateDate as a date field (YYYY-MM-DD),
            # not a full datetime; treat it as date-only filter to avoid missing changes.
            # If your environment exposes a datetime field, set updated_at_field accordingly.
            since_date = since.astimezone(timezone.utc).date().isoformat()
            filters.append(f"{entity.updated_at_field} ge '{since_date}'")

        if entity.extra_filter:
            filters.append(f"({entity.extra_filter})")

        if filters:
            params.append("$filter=" + " and ".join(filters))

        return "/b1s/v1/" + entity.endpoint + "?" + "&".join(params)

    async def fetch(
        self,
        entity: ErpEntitySpec,
        since: Optional[datetime],
        page_size: int = 200,
    ) -> Iterable[Dict[str, Any]]:
        await self._ensure_session()

        skip = 0
        while True:
            url = self._build_odata_query(entity, since=since, top=page_size, skip=skip)

            # Basic retry w/ backoff
            for attempt in range(5):
                try:
                    r = await self._client.get(url, cookies=self._session_cookies)
                    if r.status_code == 401:
                        # Session expired
                        self._session_cookies = {}
                        await self._login()
                        continue
                    r.raise_for_status()
                    data = r.json()
                    break
                except Exception:
                    if attempt == 4:
                        raise
                    await asyncio.sleep(0.5 * (2 ** attempt))

            values = data.get("value", [])
            if not values:
                return

            for rec in values:
                yield rec

            # Continue paging
            if len(values) < page_size:
                return
            skip += page_size
