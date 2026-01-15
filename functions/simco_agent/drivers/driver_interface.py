from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from simco_agent.drivers.common.models import TelemetryPoint

class DriverInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize driver with configuration (ip, port, etc).
        """
        self.config = config

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the device.
        Returns True if successful.
        """
        pass

    @abstractmethod
    async def disconnect(self):
        """
        Close connection.
        """
        pass

    @abstractmethod
    async def collect_metrics(self) -> List[TelemetryPoint]:
        """
        Poll the device and return a list of normalized TelemetryPoints.
        """
        pass
