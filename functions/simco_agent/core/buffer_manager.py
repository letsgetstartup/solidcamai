import sqlite3
import json
import hashlib
import time
import os
from typing import List, Dict, Any, Tuple, Optional
from simco_agent.config import settings

class BufferManager:
    """Manages a durable store-and-forward queue using SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.BUFFER_DB
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_buffer (
                    id TEXT PRIMARY KEY,
                    created_at REAL,
                    payload_json TEXT,
                    status TEXT DEFAULT 'queued',
                    attempt_count INTEGER DEFAULT 0,
                    last_attempt_at REAL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON telemetry_buffer(status)")
            # Cleanup stale in_flight records on startup
            conn.execute("UPDATE telemetry_buffer SET status = 'queued' WHERE status = 'in_flight'")
            conn.commit()

    def _generate_id(self, payload: Dict[str, Any]) -> str:
        """Generates a deterministic ID for idempotency using shared logic."""
        from simco_common.id import generate_record_id
        
        # Use payload's IDs if available (from Ingestor/State), else fallback to settings
        tenant_id = payload.get("tenant_id") or settings.__dict__.get("TENANT_ID", "local-dev-tenant")
        site_id = payload.get("site_id") or settings.__dict__.get("SITE_ID", "local-site-01")
        
        # Ensure payload has these for the cloud
        payload["tenant_id"] = tenant_id
        payload["site_id"] = site_id
        payload["timestamp"] = payload.get("timestamp") or datetime.utcnow().isoformat()
        
        return generate_record_id(
            tenant_id=tenant_id,
            site_id=site_id,
            machine_id=payload.get("machine_id", "unknown"),
            timestamp=payload["timestamp"],
            core_metrics=payload
        )

    def enqueue(self, payload: Dict[str, Any]) -> str:
        """Enqueues a telemetry payload with deterministic ID."""
        # Ensure we have a timestamp
        from datetime import datetime
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.utcnow().isoformat()
        
        record_id = self._generate_id(payload)
        created_at = time.time()
        payload_json = json.dumps(payload)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO telemetry_buffer (id, created_at, payload_json) VALUES (?, ?, ?)",
                    (record_id, created_at, payload_json)
                )
                conn.commit()
            return record_id
        except Exception as e:
            print(f"Failed to enqueue record: {e}")
            return None

    def reserve_batch(self, limit: int) -> List[Tuple[str, Dict[str, Any]]]:
        """Reserves a batch of records for transmission by marking them 'in_flight'."""
        batch = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT id, payload_json FROM telemetry_buffer WHERE status = 'queued' ORDER BY created_at ASC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            ids = [row['id'] for row in rows]
            
            if ids:
                placeholders = ','.join(['?'] * len(ids))
                conn.execute(
                    f"UPDATE telemetry_buffer SET status = 'in_flight', last_attempt_at = ?, attempt_count = attempt_count + 1 WHERE id IN ({placeholders})",
                    (time.time(), *ids)
                )
                conn.commit()
                
            for row in rows:
                batch.append((row['id'], json.loads(row['payload_json'])))
        return batch

    def mark_sent(self, ids: List[str]):
        """Permanently removes sent records from the buffer."""
        if not ids: return
        placeholders = ','.join(['?'] * len(ids))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"DELETE FROM telemetry_buffer WHERE id IN ({placeholders})", ids)
            conn.commit()

    def release(self, ids: List[str]):
        """Releases records back to 'queued' state if transmission fails."""
        if not ids: return
        placeholders = ','.join(['?'] * len(ids))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE telemetry_buffer SET status = 'queued' WHERE id IN ({placeholders})", ids)
            conn.commit()

    def stats(self) -> Dict[str, Any]:
        """Returns buffer health and usage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM telemetry_buffer WHERE status = 'queued'")
            queued_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT MIN(created_at) FROM telemetry_buffer WHERE status = 'queued'")
            oldest_ts = cursor.fetchone()[0]
            oldest_age = (time.time() - oldest_ts) if oldest_ts else 0
            
            results = {
                "queued_count": queued_count,
                "oldest_age_sec": round(oldest_age, 2),
                "db_path": self.db_path
            }
            
            from simco_agent.observability.metrics import edge_metrics
            edge_metrics.gauge("edge.buffer.queued_count", results["queued_count"])
            edge_metrics.gauge("edge.buffer.oldest_age_sec", results["oldest_age_sec"])
            
            return results
