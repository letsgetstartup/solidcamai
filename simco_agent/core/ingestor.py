import asyncio
import json
import logging
import aiofiles
from typing import List
from ..config import settings
from ..schemas import MachineInfo, TelemetryPayload
from ..drivers.factory import DriverFactory

logger = logging.getLogger("simco_agent.ingestor")

class Ingestor:
    def __init__(self):
        self.buffer_file = settings.BUFFER_FILE

    async def ingest_cycle(self, machines: List[MachineInfo]):
        """Polls all machines concurrently."""
        tasks = [self._process_machine(machine) for machine in machines if machine.status != "offline"]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_payloads = [r for r in results if isinstance(r, TelemetryPayload)]
        if valid_payloads:
            await self._buffer_data(valid_payloads)

    async def _process_machine(self, machine: MachineInfo) -> TelemetryPayload:
        try:
            driver = DriverFactory.get_driver(machine.vendor, machine.ip)
            if not driver:
                logger.warning(f"No driver found for {machine.vendor} at {machine.ip}")
                return None

            raw_data = await driver.read_telemetry()
            
            # Anomaly Detection Logic (Edge AI)
            is_anomaly = raw_data.get('spindle_load', 0) > settings.SPINDLE_LOAD_THRESHOLD
            
            payload = TelemetryPayload(
                machine_id=machine.mac if machine.mac != "Unknown" else machine.ip,
                status=raw_data.get('status', 'UNKNOWN'),
                spindle_load=raw_data.get('spindle_load', 0.0),
                feed_rate=raw_data.get('feed_rate', 0.0),
                program_name=raw_data.get('program_name'),
                anomaly=is_anomaly
            )
            return payload

        except Exception as e:
            logger.error(f"Error polling {machine.ip}: {e}")
            return None

    async def _buffer_data(self, payloads: List[TelemetryPayload]):
        try:
            async with aiofiles.open(self.buffer_file, mode='a') as f:
                for p in payloads:
                    # dump_json method pydantic v2
                    await f.write(p.model_dump_json() + "\n")
            logger.info(f"Buffered {len(payloads)} records.")
        except Exception as e:
            logger.error(f"Failed to buffer data: {e}")
