from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List

from .connectors.base import ErpConnector, ErpEntitySpec
from .bq_writer import ErpBigQueryWriter, make_envelope

@dataclass
class EntitySyncState:
    last_successful_sync_ts: Optional[datetime] = None
    last_source_updated_at_seen: Optional[datetime] = None
    last_error: Optional[str] = None

class ErpIngestionOrchestrator:
    """
    Provider-agnostic ingestion loop:
    - For each entity: fetch incremental records since watermark
    - Write to BigQuery raw envelope table
    - Update watermark
    """

    def __init__(self, writer: ErpBigQueryWriter):
        self.writer = writer

    async def sync_entity(
        self,
        *,
        connector: ErpConnector,
        tenant_id: str,
        connection_id: str,
        source_system: str,
        entity: ErpEntitySpec,
        state: EntitySyncState,
        page_size: int = 200,
    ) -> EntitySyncState:
        since = state.last_source_updated_at_seen or state.last_successful_sync_ts

        max_seen: Optional[datetime] = state.last_source_updated_at_seen
        batch: List[Dict[str, Any]] = []

        try:
            async for rec in connector.fetch(entity, since=since, page_size=page_size):
                pk = rec.get(entity.primary_key_field)
                if pk is None:
                    # Skip malformed ERP record
                    continue

                # Best effort parse of updated_at; field types vary
                updated_at = _parse_updated_at(rec.get(entity.updated_at_field)) if entity.updated_at_field else None
                if updated_at and (max_seen is None or updated_at > max_seen):
                    max_seen = updated_at

                batch.append(make_envelope(
                    tenant_id=tenant_id,
                    source_system=source_system,
                    connection_id=connection_id,
                    entity=entity.name,
                    source_pk=str(pk),
                    payload=rec,
                    source_updated_at=updated_at,
                ))

                if len(batch) >= 500:
                    self.writer.stream_envelopes(batch)
                    batch.clear()

            if batch:
                self.writer.stream_envelopes(batch)

            return EntitySyncState(
                last_successful_sync_ts=datetime.now(timezone.utc),
                last_source_updated_at_seen=max_seen or state.last_source_updated_at_seen,
                last_error=None,
            )

        except Exception as e:
            return EntitySyncState(
                last_successful_sync_ts=state.last_successful_sync_ts,
                last_source_updated_at_seen=state.last_source_updated_at_seen,
                last_error=str(e),
            )

def _parse_updated_at(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    # Common patterns: "2026-01-13" or "2026-01-13T12:34:56Z"
    if isinstance(v, str):
        try:
            if "T" in v:
                return datetime.fromisoformat(v.replace("Z", "+00:00")).astimezone(timezone.utc)
            return datetime.fromisoformat(v).replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None

async def _aiter(iterable):
    for x in iterable:
        yield x
