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

    async def close(self):
        """Alias for disconnect."""
        await self.disconnect()

    @abstractmethod
    async def read_telemetry(self) -> Dict[str, Any]:
        """Read current machine state."""
        pass

    @abstractmethod
    async def healthcheck(self) -> Dict[str, Any]:
        """Check driver and machine connection health."""
        pass

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw telemetry data into a standard format."""
        # Default implementation returns raw data
        return raw_data
