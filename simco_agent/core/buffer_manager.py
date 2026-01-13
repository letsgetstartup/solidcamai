import json
import logging
from sqlalchemy.future import select
from sqlalchemy import delete
from simco_agent.db import AsyncSessionLocal, TelemetryBuffer

logger = logging.getLogger(__name__)

class BufferManager:
    def __init__(self, max_size_mb=100):
        self.max_size_mb = max_size_mb

    async def write(self, data: dict):
        """
        Persist telemetry record to DB (WAL).
        """
        try:
            payload = json.dumps(data)
            # In a real WAL, we might check size first, but SQLite handles decent volumes.
            async with AsyncSessionLocal() as db:
                record = TelemetryBuffer(payload_json=payload)
                db.add(record)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to buffer data: {e}")

    async def read_batch(self, batch_size=50):
        """
        Read oldest N records.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TelemetryBuffer).order_by(TelemetryBuffer.id.asc()).limit(batch_size)
            )
            rows = result.scalars().all()
            return rows

    async def ack_batch(self, ids: list[int]):
        """
        Remove confirmed records.
        """
        if not ids:
            return
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(TelemetryBuffer).where(TelemetryBuffer.id.in_(ids))
            )
            await db.commit()
            
buffer_manager = BufferManager()
