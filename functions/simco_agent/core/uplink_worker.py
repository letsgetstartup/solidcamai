import asyncio
import logging
import requests
import time
import random
from typing import Optional
from simco_agent.config import settings
from simco_agent.core.buffer_manager import BufferManager

logger = logging.getLogger("simco_agent.uplink")

class UplinkWorker:
    """Background worker for reliable batch uploads to the cloud."""

    def __init__(self, buffer_manager: Optional[BufferManager] = None):
        self.bm = buffer_manager or BufferManager()
        self.ingest_url = settings.INGEST_URL
        self.batch_size = settings.UPLOAD_BATCH_SIZE
        self.interval = settings.UPLOAD_INTERVAL_SECONDS
        self.timeout = settings.UPLOAD_TIMEOUT_SECONDS
        self.running = False
        self.backoff_count = 0

    async def run(self):
        """Main upload loop."""
        self.running = True
        logger.info(f"UplinkWorker started. Target: {self.ingest_url}")
        
        while self.running:
            try:
                # 1. Backoff if needed
                if self.backoff_count > 0:
                    wait = min(300, (2 ** self.backoff_count) + random.uniform(0, 1))
                    logger.debug(f"Backing off for {wait:.2f}s...")
                    await asyncio.sleep(wait)

                # 2. Reserve Batch
                batch = self.bm.reserve_batch(self.batch_size)
                if not batch:
                    await asyncio.sleep(self.interval)
                    continue

                # 3. Upload
                ids = [item[0] for item in batch]
                payloads = [item[1] for item in batch]
                
                # Injected deterministic id for backend idempotency
                # record_id = {device_id}:{sqlite_row_id}
                from simco_agent.core.device_state import DeviceState
                device_id = DeviceState().device_id
                
                for p, row_id in zip(payloads, ids):
                    if "record_id" not in p or not p["record_id"]:
                        p["record_id"] = f"{device_id}:{row_id}"

                success = await self._upload_batch({"records": payloads})
                from simco_agent.observability.metrics import edge_metrics
                
                # 4. Success/Failure Handling
                if success:
                    self.bm.mark_sent(ids)
                    self.backoff_count = 0
                    logger.info(f"Successfully uploaded batch of {len(ids)} records.")
                    edge_metrics.counter("edge.uplink.success_count", len(ids))
                    edge_metrics.gauge("edge.uplink.last_success_ts", time.time())
                else:
                    self.bm.release(ids)
                    self.backoff_count += 1
                    logger.warning(f"Batch upload failed. Consecutive failures: {self.backoff_count}")
                    edge_metrics.counter("edge.uplink.failure_count", 1)
                
                # 5. Periodic Stats Emission
                self.bm.stats()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"UplinkWorker loop error: {e}")
                await asyncio.sleep(self.interval)

    async def _upload_batch(self, batch_dict: dict) -> bool:
        """Performs the actual HTTP POST."""
        loop = asyncio.get_event_loop()
        try:
            # Wrap blocking requests call in run_in_executor
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(
                    self.ingest_url, 
                    json=batch_dict, 
                    timeout=self.timeout
                )
            )
            return response.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"Batch upload request failed: {e}")
            return False

    def stop(self):
        self.running = False
