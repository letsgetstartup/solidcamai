import sqlite3
import json
import logging
import os
import uuid
from typing import List, Tuple, Dict
from dataclasses import asdict
from simco_agent.drivers.common.models import TelemetryPoint

logger = logging.getLogger(__name__)

class TelemetryBuffer:
    def __init__(self, db_path: str = "simco_agent.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS buffer (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        payload TEXT,
                        idempotency_key TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except Exception as e:
            logger.error(f"Failed to init buffer DB: {e}")

    def push(self, points: List[TelemetryPoint]):
        if not points:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Batch insert
                rows = []
                for p in points:
                    # Create unique idempotency key for this point
                    # For now just uuid, but could be hash of content+time
                    idem_key = str(uuid.uuid4())
                    payload = json.dumps(asdict(p))
                    rows.append((payload, idem_key))
                
                conn.executemany("INSERT INTO buffer (payload, idempotency_key) VALUES (?, ?)", rows)
                logger.debug(f"Buffered {len(points)} points")
        except Exception as e:
            logger.error(f"Failed to buffer points: {e}")

    def pop_chunk(self, limit: int = 100) -> Tuple[List[int], List[dict]]:
        """
        Returns (list of IDs, list of payload dicts)
        """
        ids = []
        payloads = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT id, payload FROM buffer ORDER BY id ASC LIMIT ?", (limit,))
                for row in cursor:
                    ids.append(row[0])
                    try:
                        payloads.append(json.loads(row[1]))
                    except:
                        pass # Corrupt JSON?
        except Exception as e:
            logger.error(f"Failed to pop chunk: {e}")
            
        return ids, payloads

    def commit_chunk(self, ids: List[int]):
        """
        Remove processed items from buffer.
        """
        if not ids:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                placeholders = ','.join('?' for _ in ids)
                conn.execute(f"DELETE FROM buffer WHERE id IN ({placeholders})", ids)
                logger.info(f"Committed {len(ids)} points from buffer")
        except Exception as e:
            logger.error(f"Failed to commit chunk: {e}")
            
    def count(self) -> int:
        try:
             with sqlite3.connect(self.db_path) as conn:
                 cursor = conn.execute("SELECT COUNT(*) FROM buffer")
                 return cursor.fetchone()[0]
        except:
            return 0
