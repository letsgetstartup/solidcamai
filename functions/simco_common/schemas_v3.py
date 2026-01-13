from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from datetime import datetime

class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class EventTypeEnum(str, Enum):
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    DRIVER_ERROR = "DRIVER_ERROR"
    CONFIG_CHANGED = "CONFIG_CHANGED"
    MACHINE_ONBOARDED = "MACHINE_ONBOARDED"

class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DriverInfo(BaseModel):
    driver_id: str
    driver_version: str

class TelemetryRecord(BaseModel):
    record_id: str = Field(..., description="Deterministic record ID for idempotency")
    tenant_id: str
    site_id: str
    machine_id: str
    timestamp: str # RFC3339/ISO8601
    status: StatusEnum
    metrics: Dict[str, Union[float, int, str, bool]]
    driver: Optional[DriverInfo] = None

class EventRecord(BaseModel):
    event_id: str = Field(..., description="Deterministic event ID for idempotency")
    tenant_id: str
    site_id: str
    machine_id: str
    timestamp: str
    type: EventTypeEnum
    severity: SeverityEnum
    details: Dict[str, Any]

class AssetRecord(BaseModel):
    tenant_id: str
    site_id: str
    machine_id: str
    controller_vendor: Optional[str] = None
    controller_model: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    last_seen: str

class MachineRegistryEntry(BaseModel):
    machine_id: str
    ip: str
    vendor: str
    status: str
    driver_id: Optional[str] = None
    last_seen: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TelemetryBatch(BaseModel):
    records: List[TelemetryRecord]

TelemetryBatch.model_rebuild()
