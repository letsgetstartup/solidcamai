from abc import ABC, abstractmethod
from typing import List
from simco_agent.drivers.common.models import TelemetryPoint

class DriverBase(ABC):
    """
    Abstract Base Class for all machine drivers.
    """
    
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
        Close connection to the device.
        """
        pass

    @abstractmethod
    async def sample(self) -> List[TelemetryPoint]:
        """
        Poll the device for current telemetry values.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Return connection status.
        """
        pass
