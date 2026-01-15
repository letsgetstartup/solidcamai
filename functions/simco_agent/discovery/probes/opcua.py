import logging
import asyncio
import socket
from typing import Optional
from simco_agent.drivers.common.models import Fingerprint
from . import ProbeInterface

logger = logging.getLogger(__name__)

class OPCUAProbe(ProbeInterface):
    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        # Without 'asyncua' library, we can only verify TCP connectivity 
        # and perhaps sending a Hello message to check header response.
        # For Phase 2, we assume if Port 4840 is open, it's OPC UA.
        # Future: Implement Python-native struct packing for OPC UA Hello.
        
        loop = asyncio.get_event_loop()
        is_open = await loop.run_in_executor(None, self._check_tcp, ip, port)
        
        if is_open:
            return Fingerprint(
                ip=ip,
                protocol="opc_ua",
                endpoint=f"opc.tcp://{ip}:{port}",
                confidence=0.8, # Good confidence based on port convention
                vendor="SIEMENS", # Default guess for OPC UA in this context, or update later
                evidence={"port_open": port, "banner": "TCP Connect Success"}
            )
        return None

    def _check_tcp(self, ip, port) -> bool:
        try:
            with socket.create_connection((ip, port), timeout=2):
                return True
        except:
            return False
