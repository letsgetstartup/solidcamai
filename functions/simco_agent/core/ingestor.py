import logging
import asyncio
from typing import List, Dict, Any, Optional
from .driver_manager import DriverManager
from ..schemas import TelemetryPayload, MachineInfo
from .device_state import DeviceState

logger = logging.getLogger("simco_agent.ingestor")

class Ingestor:
    """Orchestrates driver execution and local buffering."""
    
    def __init__(self, state: Optional[DeviceState] = None):
        self.dm = DriverManager()
        self.state = state or DeviceState()

    async def _buffer_data(self, records: List[Dict[str, Any]]):
        try:
            from .buffer_manager import BufferManager
            bm = BufferManager()
            for r in records:
                bm.enqueue(r)
            logger.info(f"Durable buffer updated with {len(records)} records.")
        except Exception as e:
            logger.error(f"Failed to buffer data to SQLite: {e}")

    async def ingest_cycle(self, machines_data: List[Dict[str, Any]]):
        """Execute a single ingestion cycle for all active machines."""
        if not self.state.is_enrolled:
            logger.warning("Ingestor: Device not enrolled. Skipping cycle.")
            return

        # Convert simple machine dicts to MachineInfo objects for DriverManager
        machine_infos = []
        for m in machines_data:
            try:
                # Ensure it has the fields required by MachineInfo
                info = MachineInfo(
                    ip=m["ip"],
                    mac=m.get("mac", "Unknown"),
                    vendor=m.get("vendor", "UNKNOWN"),
                    status=m.get("status", "active"),
                    driver_id=m.get("driver_id")
                )
                machine_infos.append(info)
            except Exception as e:
                logger.error(f"Invalid machine data for {m.get('machine_id')}: {e}")

        if not machine_infos:
            return

        # 1. Poll machines in parallel
        from simco_agent.observability.metrics import edge_metrics
        import time
        start_poll = time.time()
        
        logger.info(f"Ingestor: Polling {len(machine_infos)} machines...")
        payloads = await self.dm.run_poll(machine_infos)
        logger.info(f"Ingestor: Received {len(payloads)} payloads.")
        
        duration = (time.time() - start_poll) * 1000
        edge_metrics.histogram("edge.ingestor.cycle_duration_ms", duration)

        # 2. Convert to v3 Records
        records = []
        tenant_id = self.state.data.get("tenant_id", "unknown_tenant")
        site_id = self.state.data.get("site_id", "unknown_site")
        device_id = self.state.device_id

        for p in payloads:
            records.append(p.to_v3_record(tenant_id, site_id, device_id))

        if records:
            await self._buffer_data(records)
