import logging
import asyncio
from typing import List, Dict, Optional, Any
from pymodbus.client import AsyncModbusTcpClient
from simco_agent.drivers.common.base_driver import DriverBase
from simco_agent.drivers.common.models import TelemetryPoint
from simco_agent.drivers.common.normalize import normalize_execution_state

logger = logging.getLogger(__name__)

class ModbusDriver(DriverBase):
    def __init__(self, endpoint: str, register_map: Dict[str, Dict] = None):
        """
        endpoint: e.g. "modbus-tcp://192.168.1.5:502"
        register_map: 
        {
          "execution_state": {"address": 100, "type": "holding"},
          "spindle_speed": {"address": 102, "type": "holding"}
        }
        """
        self.endpoint = endpoint
        # Parse host/port from endpoint string "modbus-tcp://host:port"
        try:
            parts = endpoint.replace("modbus-tcp://", "").split(":")
            self.host = parts[0]
            self.port = int(parts[1]) if len(parts) > 1 else 502
        except:
            self.host = "localhost"
            self.port = 502
            
        self.client = AsyncModbusTcpClient(self.host, port=self.port)
        self._connected = False
        
        # Default simple map
        self.register_map = register_map or {
            "execution_state": {"address": 100, "type": "holding"},
            "availability": {"address": 101, "type": "holding"},
            "spindle_speed": {"address": 102, "type": "holding"}
        }

    async def connect(self) -> bool:
        try:
            self._connected = await self.client.connect()
            return self._connected
        except Exception as e:
            logger.error(f"Modbus connect error: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        try:
            self.client.close()
        except: pass
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def sample(self) -> List[TelemetryPoint]:
        if not self._connected:
            return []
            
        points = []
        import datetime
        now = datetime.datetime.utcnow().isoformat()
        
        try:
            for name, config in self.register_map.items():
                addr = config.get("address")
                reg_type = config.get("type", "holding")
                
                # Naive implementation: read one by one. In prod, group reads.
                val = None
                
                if reg_type == "holding":
                     rr = await self.client.read_holding_registers(addr, 1)
                     if not rr.isError():
                         val = rr.registers[0]
                elif reg_type == "input":
                     rr = await self.client.read_input_registers(addr, 1)
                     if not rr.isError():
                         val = rr.registers[0]
                         
                if val is not None:
                     # Mapping logic (very simple demo)
                     if name == "execution_state":
                         # 1=ACTIVE, 2=READY, 0=STOPPED
                         state_map = {1: "ACTIVE", 2: "READY", 0: "STOPPED"}
                         val = state_map.get(val, "UNKNOWN")
                     elif name == "availability":
                         val = "AVAILABLE" if val > 0 else "UNAVAILABLE"
                         
                     points.append(TelemetryPoint(name=name, value=val, timestamp=now))
                     
        except Exception as e:
            logger.error(f"Modbus sample error: {e}")
            # self._connected = False # Don't disconnect on transient read error? safely close?
            
        return points
