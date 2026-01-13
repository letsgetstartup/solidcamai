import asyncio
import logging
import platform
import socket
import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class HeartbeatWorker:
    def __init__(self, config_manager, uplink_client, interval_seconds: int = 30):
        self.config_manager = config_manager
        self.uplink_client = uplink_client # TODO: Need a unified HTTP client for control plane
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Heartbeat worker started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat worker stopped")

    async def _loop(self):
        while self._running:
            try:
                await self._send_heartbeat()
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
            
            await asyncio.sleep(self.interval_seconds)

    async def _send_heartbeat(self):
        gateway_id = self.config_manager.get_gateway_id()
        if not gateway_id:
            logger.debug("Skipping heartbeat: No Gateway ID yet")
            return

        payload = {
            "uptime_seconds": self._get_uptime(), # Placeholder
            "local_ip": self._get_local_ip(),
            "agent_version": "3.1.0",
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        # Using the unified cloud client (which handles auth/mTLS)
        # Assuming uplink_client has a method for control plane requests
        # For now, we stub the call logic or rely on the caller to provide a client wrapper
        if hasattr(self.uplink_client, "post_control_plane"):
             await self.uplink_client.post_control_plane(
                 f"/gateways/{gateway_id}/heartbeat", 
                 json=payload
             )
        else:
             logger.warning("Uplink client missing post_control_plane method")

    def _get_local_ip(self) -> str:
        try:
            # Dummy connection to determine interface
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _get_uptime(self) -> int:
        # TODO: Implement real uptime
        return 0
