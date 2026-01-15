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
        self.interval = settings.UPLOAD_INTERVAL_SECONDS
        self.timeout = settings.UPLOAD_TIMEOUT_SECONDS
        self.running = False
        self.backoff_count = 0

    def submit_batch(self, batch):
        """Public API to queue a batch."""
        self.bm.push(batch)

    async def run(self):
        """Main upload loop."""
        self.running = True
        logger.info(f"UplinkWorker started. Target: {self.ingest_url}")
        
        from simco_agent.core.device_state import DeviceState
        
        while self.running:
            try:
                # 1. Backoff if needed
                if self.backoff_count > 0:
                    wait = min(300, (2 ** self.backoff_count) + random.uniform(0, 1))
                    logger.debug(f"Backing off for {wait:.2f}s...")
                    await asyncio.sleep(wait)

                # 2. Peek Batch (Persisted Queue)
                batch = self.bm.peek()
                
                if not batch:
                    await asyncio.sleep(self.interval)
                    continue

                # 3. Upload
                # Serialize back to dict for sending
                from dataclasses import asdict
                payload = asdict(batch)
                
                # PR11: Idempotency Key
                headers = {
                    "Authorization": f"Bearer {DeviceState().gateway_token}",
                    "Content-Type": "application/json",
                    "X-Idempotency-Key": batch.uuid
                }

                success = await self._upload_batch(payload, headers)
                
                # 4. Success/Failure Handling
                if success:
                    self.bm.ack(batch.uuid) # Delete from buffer
                    self.backoff_count = 0
                    logger.info(f"Successfully uploaded batch {batch.uuid} ({len(batch.records)} pts).")
                else:
                    # Do NOT delete. Backoff and retry (Head of Line blocking is intended for strict ordering? Or maybe just retry same batch)
                    # For now: Head of Line blocking ensures order.
                    self.backoff_count += 1
                    logger.warning(f"Batch {batch.uuid} upload failed. Retry #{self.backoff_count}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"UplinkWorker loop error: {e}")
                await asyncio.sleep(self.interval)

    async def _upload_batch(self, payload: dict, headers: dict) -> bool:
        """Performs the actual HTTP POST."""
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(
                    self.ingest_url, 
                    json=payload, 
                    headers=headers,
                    timeout=self.timeout
                )
            )
            return response.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"Batch upload request failed: {e}")
            return False

    def stop(self):
        self.running = False
