from abc import ABC, abstractmethod
from typing import Optional
from simco_agent.drivers.common.models import Fingerprint

class ProbeInterface(ABC):
    @abstractmethod
    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        """
        Executes the probe against the target.
        Returns a Fingerprint if successful, None otherwise.
        """
        pass
