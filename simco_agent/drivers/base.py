from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseDriver(ABC):
    def __init__(self, ip: str, port: int = 0):
        self.ip = ip
        self.port = port
        self.connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the machine."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Close connection."""
        pass

    @abstractmethod
    async def read_telemetry(self) -> Dict[str, Any]:
        """Read current machine state."""
        pass
