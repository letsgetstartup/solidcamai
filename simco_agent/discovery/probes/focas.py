import logging
import asyncio
import socket
from typing import Optional
from simco_agent.drivers.common.models import Fingerprint
from . import ProbeInterface

logger = logging.getLogger(__name__)

class FocasProbe(ProbeInterface):
    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        # Focas is binary RPC. Without DLLs/Libs, we rely on port check.
        # Port 8193 is standard.
        loop = asyncio.get_event_loop()
        is_open = await loop.run_in_executor(None, self._check_tcp, ip, port)
        
        if is_open:
            return Fingerprint(
                ip=ip,
                protocol="fanuc_focas",
                endpoint=f"{ip}:{port}",
                confidence=0.7,
                vendor="FANUC",
                evidence={"port_open": port}
            )
        return None

    def _check_tcp(self, ip, port) -> bool:
        try:
            with socket.create_connection((ip, port), timeout=2):
                return True
        except:
            return False
