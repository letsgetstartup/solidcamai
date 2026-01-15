import logging
import asyncio
from typing import Optional
from asyncua import Client, ua
from simco_agent.drivers.common.models import Fingerprint

logger = logging.getLogger(__name__)

class OPCUAProbe:
    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout

    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        """
        Probes an IP:Port for OPC UA compatibility (GetEndpoints + ServerStatus).
        """
        endpoint_url = f"opc.tcp://{ip}:{port}"
        client = Client(url=endpoint_url)
        # Set session timeout
        client.session_timeout = self.timeout * 1000
        
        try:
            # We use a context manager to ensure clean disconnect
            # asyncua connect might hang if host unreachable, so wrap in timeout
            async with asyncio.timeout(self.timeout):
                async with client:
                    # If we connected, we already have good confidence
                    # Try reading ServerStatus to confirm it's a happy server
                    
                    try:
                        # Direct read of BuildInfo properties via helper node logic in asyncua
                        # client.nodes.server should give the Server Object (i=2253)
                        # We can try to access children if known, or use get_child if needed.
                        # However, asyncua exposes server info nodes conveniently
                        
                        # Note: Different servers might expose standard nodes differently.
                        # But ManufacturerName (i=2263) is standard part of BuildInfo.
                        
                        # We try rigid node traversal or known IDs
                        # ManufacturerName = i=2263
                        # ProductName = i=2261
                        # SoftwareVersion = i=2264
                        
                        # Reading values directly
                        manufacturer = await (client.get_node(ua.NodeId(2263, 0))).read_value()
                        product = await (client.get_node(ua.NodeId(2261, 0))).read_value()
                        software_ver = await (client.get_node(ua.NodeId(2264, 0))).read_value()
                        
                    except Exception as e:
                        logger.debug(f"OPC UA BuildInfo read failed: {e}")
                        manufacturer = None
                        product = None
                        software_ver = None
                        
                    return Fingerprint(
                        ip=ip,
                        protocol="opcua",
                        vendor=manufacturer,
                        model=product,
                        controller_version=software_ver,
                        endpoint=endpoint_url,
                        confidence=0.95,
                        evidence={"endpoint": endpoint_url}
                    )
                    
        except asyncio.TimeoutError:
            logger.debug(f"OPC UA probe timeout for {endpoint_url}")
            return None
        except Exception as e:
            # Check for specifically ConnectionRefused or similar
            logger.error(f"OPC UA probe failed for {endpoint_url}: {e}")
            print(f"DEBUG PROBE FAIL: {e}")
            import traceback
            traceback.print_exc()
            return None
