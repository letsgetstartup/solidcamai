from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud import bigquery

class ErpBigQueryWriter:
    """
    Writes ERP records to a raw envelope table in BigQuery.
    Uses deterministic insertIds to reduce duplicate streaming inserts.
    """

    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"

    @staticmethod
    def _insert_id(tenant_id: str, source_system: str, entity: str, source_pk: str, source_updated_at: Optional[str]) -> str:
        raw = f"{tenant_id}|{source_system}|{entity}|{source_pk}|{source_updated_at or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def stream_envelopes(self, envelopes: List[Dict[str, Any]]) -> None:
        row_ids = [
            self._insert_id(
                e["tenant_id"],
                e["source_system"],
                e["entity"],
                e["source_pk"],
                e.get("source_updated_at"),
            )
            for e in envelopes
        ]

        errors = self.client.insert_rows_json(self.table_ref, envelopes, row_ids=row_ids)
        if errors:
            raise RuntimeError(f"BigQuery insert errors: {errors}")

def make_envelope(
    tenant_id: str,
    source_system: str,
    connection_id: str,
    entity: str,
    source_pk: str,
    payload: Dict[str, Any],
    source_updated_at: Optional[datetime],
) -> Dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "source_system": source_system,
        "connection_id": connection_id,
        "entity": entity,
        "source_pk": str(source_pk),
        "source_updated_at": source_updated_at.astimezone(timezone.utc).isoformat() if source_updated_at else None,
        "ingest_ts": datetime.now(timezone.utc).isoformat(),
        "payload": payload,  # BigQuery JSON column accepts dicts via client lib
    }
