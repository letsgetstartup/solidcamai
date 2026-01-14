import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from simco_agent.drivers.driver_interface import DriverInterface
from simco_agent.drivers.common.models import TelemetryPoint, SignalQuality

logger = logging.getLogger(__name__)

try:
    from asyncua import Client, ua
except ImportError:
    logger.warning("asyncua not installed. Siemens driver will not function.")
    Client = None
    ua = None

class SiemensOPCUADriver(DriverInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ip = config.get("ip")
        self.port = config.get("port", 4840)
        self.endpoint = f"opc.tcp://{self.ip}:{self.port}"
        self.username = config.get("username")
        self.password = config.get("password")
        self.client = None
        self._connected = False

    async def connect(self) -> bool:
        if not Client:
            logger.error("asyncua library missing")
            return False
            
        try:
            self.client = Client(url=self.endpoint)
            if self.username and self.password:
                self.client.set_user(self.username)
                self.client.set_password(self.password)
                
            await self.client.connect()
            self._connected = True
            return True
        except Exception as e:
            logger.warning(f"Siemens OPC UA connect failed: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        if self.client and self._connected:
            try:
                await self.client.disconnect()
            except:
                pass
        self._connected = False

    async def collect_metrics(self) -> List[TelemetryPoint]:
        if not self._connected or not self.client:
            return []
            
        points = []
        ts = datetime.utcnow().isoformat()
        
        try:
            # Map of internal name -> NodeID
            # These are example NodeIDs for a Siemens 840D sl / Sinumerik
            # In production, these might be configurable per machine
            nodes_to_read = {
                "spindle_speed":           "ns=2;s=/Channel/Spindle/speed", # Logic override?
                "spindle_speed_override":  "ns=2;s=/Channel/Spindle/speedOvr",
                "feed_rate":               "ns=2;s=/Channel/Spindle/feedRate",
                "execution_state":         "ns=2;s=/Channel/State/progStatus", # STOPPED, ABORTED, RUNNING
                "program_name":            "ns=2;s=/Channel/ProgramInfo/progName",
                "controller_mode":         "ns=2;s=/Bag/State/opMode"
            }
            
            # Read values
            # Optimization: Use client.read_values(nodes) if we had Node objects
            # For simplicity in this PR, we read one by one or create Node objects
            
            for key, node_id in nodes_to_read.items():
                try:
                    node = self.client.get_node(node_id)
                    val = await node.read_value()
                    
                    # Transform/Normalize if needed
                    if key == "execution_state":
                         # Simplify Siemens states (0=ROV, 1=ROV...) -> Simco Enum
                         # This is just a pass-through for now
                         val = str(val)

                    points.append(TelemetryPoint(
                        name=key,
                        value=val,
                        timestamp=ts
                    ))
                except Exception as node_err:
                    # Node might not exist on this specific machine version
                    # logger.debug(f"Missing node {node_id}: {node_err}")
                    pass

            return points

        except Exception as e:
            logger.error(f"Error collecting metrics from Siemens: {e}")
            # Try reconnect logic usually goes here or in manager
            self._connected = False
            return []
