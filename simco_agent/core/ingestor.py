import logging
from typing import List, Dict, Any
from .driver_manager import DriverManager
from ..schemas import TelemetryPayload

logger = logging.getLogger("simco_agent.ingestor")

class Ingestor:
    """Orchestrates driver execution and local buffering."""
    
    def __init__(self):
        self.dm = DriverManager()

    async def _buffer_data(self, payloads: List[TelemetryPayload]):
        try:
            from .buffer_manager import BufferManager
            bm = BufferManager()
            for p in payloads:
                bm.enqueue(p.model_dump())
            logger.info(f"Durable buffer updated with {len(payloads)} records.")
        except Exception as e:
            logger.error(f"Failed to buffer data to SQLite: {e}")

    async def ingest_cycle(self, machines: List[Dict[str, Any]]):
        """Execute a single ingestion cycle for all active machines."""
        payloads = []
        for m in machines:
            try:
                import time
                from simco_agent.observability.metrics import edge_metrics
                start_poll = time.time()
                data = await self.dm.execute_driver(m["driver_id"], m)
                duration = (time.time() - start_poll) * 1000
                edge_metrics.histogram("edge.driver.poll.duration_ms", duration, labels={"driver_id": m["driver_id"]})
                
                if data:
                    payload = TelemetryPayload(
                        machine_id=m["machine_id"],
                        **data
                    )
                    payloads.append(payload)
            except Exception as e:
                logger.error(f"Ingestion failed for machine {m.get('machine_id')}: {e}")
                edge_metrics.counter("edge.driver.poll.timeout_count", 1, labels={"driver_id": m["driver_id"]})

        if payloads:
            await self._buffer_data(payloads)
