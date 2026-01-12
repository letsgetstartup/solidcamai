from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class MachineInfo(BaseModel):
    ip: str
    mac: str
    vendor: str
    status: Literal["discovered", "active", "offline"] = "discovered"
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    driver_type: Optional[str] = None

class TelemetryPayload(BaseModel):
    machine_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: Literal["ACTIVE", "IDLE", "ALARM", "OFFLINE"]
    spindle_load: float = Field(..., ge=0, le=120, description="Percentage load")
    feed_rate: float = Field(default=0.0)
    program_name: Optional[str] = None
    anomaly: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
