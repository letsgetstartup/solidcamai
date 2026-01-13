import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DiscoveryPolicy(BaseModel):
    mode: str = "hybrid"  # active, passive, hybrid, manual_only
    active_enabled: bool = True
    active_rate_limit_pps: int = 10
    allowed_subnets: List[str] = []
    port_probes: List[int] = [8193, 502, 44818] # Fanuc, Modbus, Ethernet/IP

    def is_active_allowed(self) -> bool:
        if self.mode == "manual_only" or self.mode == "passive":
            return False
        return self.active_enabled

    def is_passive_allowed(self) -> bool:
        return self.mode in ["passive", "hybrid"]

    def log_decision(self):
        logger.info(f"DiscoveryPolicy Decision: mode={self.mode}, active={self.active_enabled}, rate_limit={self.active_rate_limit_pps}pps")
        if self.allowed_subnets:
            logger.info(f"DiscoveryPolicy Subnets: {self.allowed_subnets}")
