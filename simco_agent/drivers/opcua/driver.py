import logging
import asyncio
from typing import List, Dict, Optional, Any
from asyncua import Client, ua
from simco_agent.drivers.common.base_driver import DriverBase
from simco_agent.drivers.common.models import TelemetryPoint
from simco_agent.drivers.common.normalize import normalize_execution_state

logger = logging.getLogger(__name__)

class OPCUADriver(DriverBase):
    def __init__(self, endpoint: str, node_map: Dict[str, str] = None):
        self.endpoint = endpoint
        self.client: Optional[Client] = None
        self._connected = False
        
        # Default map assumes a simulation Namespace Index=2
        # Use simple string IDs "ns=2;s=Execution"
        self.node_map = node_map or {
            "execution_state": "ns=2;s=Execution",
            "spindle_speed": "ns=2;s=SpindleSpeed",
            "availability": "ns=2;s=Availability",
            "part_count": "ns=2;s=PartCount"
        }

    async def connect(self) -> bool:
        try:
            self.client = Client(url=self.endpoint)
            await self.client.connect()
            self._connected = True
            return True
        except Exception as e:
            logger.error(f"OPC UA connect error: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self.client:
            try:
                await self.client.disconnect()
            except: pass
        self._connected = False
        self.client = None

    def is_connected(self) -> bool:
        return self._connected

    async def sample(self) -> List[TelemetryPoint]:
        if not self._connected or not self.client:
            return []

        points = []
        try:
            # We can optimise this with read_values(list_of_nodes)
            # But asyncua API for that requires Node objects.
            
            # 1. Resolve nodes (could cache these)
            # For simplicity, individual reads for now or simple loop
            
            import datetime
            now = datetime.datetime.utcnow().isoformat()

            for name, node_id_str in self.node_map.items():
                try:
                    node = self.client.get_node(node_id_str)
                    val = await node.read_value()
                    
                    # Normalize if needed
                    if name == "execution_state":
                        val = normalize_execution_state(str(val))
                    
                    points.append(TelemetryPoint(
                        name=name,
                        value=val,
                        timestamp=now
                    ))
                except Exception as e:
                    logger.debug(f"Failed to read node {name} ({node_id_str}): {e}")

        except Exception as e:
            logger.error(f"OPC UA sample failed: {e}")
            self._connected = False
        
        return points
