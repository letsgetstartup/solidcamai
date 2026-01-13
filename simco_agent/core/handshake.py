import asyncio
import logging
import socket
from typing import Optional, Dict, Any
from simco_common.schemas_v3 import HandshakeResult, ControllerVendor, ProtocolEnum

logger = logging.getLogger(__name__)

class HandshakeService:
    def __init__(self):
        pass

    async def probe(self, ip: str) -> Optional[HandshakeResult]:
        """
        Attempts to identify the machine at the given IP.
        Strategies:
        1. OPC UA (Port 4840) -> Siemens
        2. MTConnect (Port 80/5000/7878) -> Haas/Generic
        3. FOCAS (Port 8193) -> Fanuc
        4. Modbus (Port 502) -> Generic IO
        """
        
        # 1. Check OPC UA
        if await self._check_port(ip, 4840):
            # In a real impl, we'd open a session and read Identity obj
            logger.info(f"OPC UA Port open on {ip}. Assuming Siemens/OPC UA.")
            return HandshakeResult(
                controller_vendor=ControllerVendor.SIEMENS,
                controller_model="Generic OPC UA",
                protocol=ProtocolEnum.OPCUA,
                endpoint={"host": ip, "port": 4840, "path": "/"},
                fingerprint_sha256="fake_sha",
                confidence=0.8
            )

        # 2. Check FOCAS
        if await self._check_port(ip, 8193):
            logger.info(f"FOCAS Port open on {ip}. Assuming Fanuc.")
            return HandshakeResult(
                controller_vendor=ControllerVendor.FANUC,
                controller_model="Fanuc Series",
                protocol=ProtocolEnum.FOCAS,
                endpoint={"host": ip, "port": 8193},
                fingerprint_sha256="fake_sha",
                confidence=0.9
            )

        # 3. Check MTConnect (various ports)
        # Haas usually 8090, 80, or 7878
        for port in [5000, 7878, 8090]:
            if await self._check_port(ip, port):
                 # Try HTTP GET /current to confirm?
                 # For now, port open is enough hint
                 logger.info(f"Port {port} open on {ip}. Suspect MTConnect.")
                 return HandshakeResult(
                    controller_vendor=ControllerVendor.HAAS, # Assumption
                    controller_model="Haas NGC",
                    protocol=ProtocolEnum.MTCONNECT,
                    endpoint={"host": ip, "port": port, "path": "/current"},
                    fingerprint_sha256="fake_sha",
                    confidence=0.6
                )

        return None

    async def _check_port(self, ip: str, port: int, timeout: float = 1.0) -> bool:
        try:
            # Run blocking socket in thread
            return await asyncio.to_thread(self._socket_connect, ip, port, timeout)
        except Exception:
            return False

    def _socket_connect(self, ip, port, timeout):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((ip, port)) == 0

handshake_service = HandshakeService()
