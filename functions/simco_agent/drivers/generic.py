import asyncio
from typing import Dict, Any
from .base import BaseDriver

class GenericProtocolDriver(BaseDriver):
    """Fallback driver for unknown or unsupported machine protocols."""
    
    async def connect(self) -> bool:
        self.connected = True
        return True

    async def disconnect(self):
        self.connected = False

    async def read_telemetry(self) -> Dict[str, Any]:
        if "HANG" in self.ip:
            await asyncio.sleep(10) # Longer than timeout
        if "FAIL" in self.ip:
            raise Exception("Simulated Failure")
        
        import random
        return {
            "status": random.choice(["ACTIVE", "IDLE", "RUNNING"]),
            "spindle_load_pct": random.uniform(20.0, 100.0), # Matches rule metric name
            "feed_rate": random.uniform(500, 2000),
            "message": "Generic Driver Active"
        }

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "protocol": "GENERIC"
        }
