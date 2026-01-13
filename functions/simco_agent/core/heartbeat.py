import asyncio
import logging
import requests
import psutil
import os
from typing import Optional
from simco_agent.config import settings
from simco_agent.core.device_state import DeviceState
from simco_agent.core.buffer_manager import BufferManager

logger = logging.getLogger("simco_agent.heartbeat")

class HeartbeatAgent:
    """Reports agent health and status to the cloud management plane."""

    def __init__(self, state: Optional[DeviceState] = None):
        self.state = state or DeviceState()
        self.interval = settings.HEARTBEAT_INTERVAL_SECONDS
        self.running = False

    async def run(self):
        self.running = True
        logger.info("HeartbeatAgent started.")
        
        while self.running:
            try:
                if not self.state.is_enrolled:
                    await asyncio.sleep(10)
                    continue

                await self._send_heartbeat()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(30)

    async def _send_heartbeat(self):
        url = f"{settings.MGMT_BASE_URL}/heartbeat"
        
        # Gather metrics
        stats = BufferManager().stats()
        disk = psutil.disk_usage('/')
        
        payload = {
            "device_id": self.state.device_id,
            "tenant_id": self.state.data.get("tenant_id"),
            "site_id": self.state.data.get("site_id"),
            "runtime_version": "2.2.0",
            "buffer_depth": stats["queued_count"],
            "disk_free_mb": disk.free // (1024 * 1024),
            "machine_count": 0, # Should be wired to registry
            "timestamp": os.times().elapsed
        }
        
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, timeout=5))
            if response.status_code == 200:
                logger.debug("Heartbeat acknowledged.")
            else:
                logger.warning(f"Heartbeat rejected: {response.status_code}")
        except Exception as e:
            logger.error(f"Heartbeat transport error: {e}")

    def stop(self):
        self.running = False
