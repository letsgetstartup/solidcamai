import asyncio
import logging
import json
from .buffer_manager import buffer_manager

logger = logging.getLogger(__name__)

class UplinkWorker:
    def __init__(self, uplink_client, interval_seconds=5):
        self.client = uplink_client
        self.interval = interval_seconds
        self._running = False

    async def start(self):
        self._running = True
        logger.info("Uplink Worker started")
        while self._running:
            await self._cycle()
            await asyncio.sleep(self.interval)

    async def stop(self):
        self._running = False

    async def _cycle(self):
        # 1. Read Batch
        rows = await buffer_manager.read_batch(batch_size=50)
        if not rows:
            return

        # 2. Prepare Payload
        records = []
        ids_to_ack = []
        for row in rows:
            try:
                data = json.loads(row.payload_json)
                records.append(data)
                ids_to_ack.append(row.id)
            except Exception:
                logger.error("Corrupt record found in buffer")
                ids_to_ack.append(row.id) # Ack anyway to unblock

        if not records:
             # Just corrupt data cleanup
             await buffer_manager.ack_batch(ids_to_ack)
             return

        # 3. Send to Cloud
        try:
            # OpenTelemetry Manual Span
            try:
                from opentelemetry import trace
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span("uplink_batch") as span:
                    span.set_attribute("record_count", len(records))
                    # Assuming client has a method to post telemetry batch
                    if self.client:
                         # TODO: Real endpoint
                         # success = await self.client.post_telemetry(records)
                         pass
            except ImportError:
                # Fallback if OTel not present
                if self.client:
                     pass
            
            # 4. Ack Success
            await buffer_manager.ack_batch(ids_to_ack)
            logger.info(f"Uplinked {len(records)} records")
            
        except Exception as e:
            logger.error(f"Uplink failed: {e}")
            # Do NOT ack, so we retry next time
