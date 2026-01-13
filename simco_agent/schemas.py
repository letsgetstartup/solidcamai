from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime
from simco_common.schemas_v3 import TelemetryRecordV3 as TelemetryRecord, StatusEnum

class MachineInfo(BaseModel):
    ip: str
    mac: str
    vendor: str
    status: Literal["discovered", "active", "offline", "MANUAL_ENROLLED"] = "discovered"
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    driver_id: Optional[str] = None

class TelemetryPayload(BaseModel):
    machine_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str
    spindle_load: float = 0.0
    feed_rate: float = 0.0
    program_name: Optional[str] = None
    anomaly: bool = False
    
    def to_v3_record(self, tenant_id: str, site_id: str, device_id: str) -> Dict[str, Any]:
        """Convert legacy payload to v3 TelemetryRecord dict."""
        return {
            "record_id": "", # To be filled by uplink or ingestion
            "tenant_id": tenant_id,
            "site_id": site_id,
            "machine_id": self.machine_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status if self.status in StatusEnum.__members__ else "UNKNOWN",
            "metrics": {
                "spindle_load": self.spindle_load,
                "feed_rate": self.feed_rate,
                "program_name": self.program_name or "",
                "anomaly": self.anomaly
            },
            "driver": None # Optional
        }

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
