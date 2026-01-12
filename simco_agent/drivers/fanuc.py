import asyncio
import random
from typing import Dict, Any
from .base import BaseDriver

class FanucDriver(BaseDriver):
    def __init__(self, ip: str):
        super().__init__(ip, port=8193)

    async def connect(self) -> bool:
        # Simulate FOCAS library connection delay
        await asyncio.sleep(0.5)
        self.connected = True
        return True

    async def disconnect(self):
        self.connected = False

    async def read_telemetry(self) -> Dict[str, Any]:
        if not self.connected:
            await self.connect()
        
        # Mocking FOCAS library calls
        return {
            "status": random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "IDLE", "IDLE", "ALARM"]),
            "spindle_load": round(random.uniform(0, 100), 2),
            "feed_rate": round(random.uniform(500, 2000), 2),
            "program_name": "O" + str(random.randint(1000, 5000))
        }
