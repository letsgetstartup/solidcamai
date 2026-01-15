import sqlite3
import json
import logging
import os
import time
from typing import List, Optional, Tuple
from dataclasses import asdict
from simco_agent.drivers.common.models import TelemetryBatch

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "telemetry_buffer.db")

class BufferManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_uuid TEXT UNIQUE,
                        payload TEXT,
                        created_at REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init buffer DB: {e}")

    def push(self, batch: TelemetryBatch):
        try:
            payload_json = json.dumps(asdict(batch))
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO telemetry_queue (batch_uuid, payload, created_at) VALUES (?, ?, ?)",
                    (batch.uuid, payload_json, time.time())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to buffer batch {batch.uuid}: {e}")

    def peek(self) -> Optional[TelemetryBatch]:
        """Get the oldest batch without removing it."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT payload FROM telemetry_queue ORDER BY id ASC LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    data = json.loads(row[0])
                    # Reconstruct batch - naive reconstruction
                    # TelemetryBatch might have complex fields, assuming dict is compatible
                    return TelemetryBatch(**data)
        except Exception as e:
            logger.error(f"Failed to peek buffer: {e}")
        return None

    def ack(self, batch_uuid: str):
        """Remove batch from buffer after successful upload."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM telemetry_queue WHERE batch_uuid = ?", (batch_uuid,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to ack batch {batch_uuid}: {e}")

    def count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM telemetry_queue")
                return cursor.fetchone()[0]
        except:
            return 0
