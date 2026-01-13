from pydantic import BaseModel, Field, constr, field_validator
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from datetime import datetime

# --- Canonical IDs (Strong Types) ---
# Using type aliases for clarity, but validated via regex in models if needed
TenantID = constr(pattern=r"^[a-z0-9-_]+$")
SiteID = constr(pattern=r"^[a-z0-9-_]+$")
GatewayID = constr(pattern=r"^[a-z0-9-_]+$")
MachineID = constr(pattern=r"^[a-z0-9-_]+$")

# --- Enums ---
class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RUNNING = "ACTIVE" # Alias
    READY = "READY"
    IDLE = "READY" # Alias
    STOPPED = "STOPPED"
    FEED_HOLD = "FEED_HOLD"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ControllerVendor(str, Enum):
    SIEMENS = "SIEMENS"
    FANUC = "FANUC"
    HAAS = "HAAS"
    HEIDENHAIN = "HEIDENHAIN"
    UNKNOWN = "UNKNOWN"

class ProtocolEnum(str, Enum):
    OPCUA = "opcua"
    MTCONNECT = "mtconnect"
    FOCAS = "focas"
    MODBUS = "modbus"

# --- Discovery & Handshake ---
class HandshakeResult(BaseModel):
    controller_vendor: ControllerVendor
    controller_model: str
    controller_version: Optional[str] = None
    serial: Optional[str] = None
    machine_name: Optional[str] = None
    protocol: ProtocolEnum
    endpoint: Dict[str, Any] # host, port, path
    fingerprint_sha256: str
    confidence: float = Field(ge=0.0, le=1.0)

# --- Telemetry ---
class QualityMetrics(BaseModel):
    source_clock_skew_ms: Optional[float] = None
    sample_period_ms: Optional[float] = None

class TelemetryRecord(BaseModel):
    record_id: str = Field(..., description="Deterministic record ID for idempotency")
    tenant_id: str
    site_id: str
    machine_id: str
    device_id: Optional[str] = Field(None, description="Edge Gateway Identity")
    timestamp: str # RFC3339/ISO8601
    status: StatusEnum
    metrics: Dict[str, Union[float, int, str, bool]] = Field(default_factory=dict)
    driver: Optional[DriverInfo] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        try:
            # Simple RFC3339/ISO8601 check
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid timestamp format. Expected RFC3339.")
        return v

class EventRecord(BaseModel):
    event_id: str = Field(..., description="Deterministic event ID for idempotency")
    tenant_id: str
    site_id: str
    machine_id: str
    device_id: Optional[str] = Field(None, description="Edge Gateway Identity")
    actor_user_id: Optional[str] = Field(None, description="User who triggered this event")
    timestamp: str
    type: EventTypeEnum
    severity: SeverityEnum
    details: Dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v):
        try:
            # Simple RFC3339/ISO8601 check
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Invalid timestamp format. Expected RFC3339.")
        return v

class TelemetryBatch(BaseModel):
    gateway_id: str
    records: List[TelemetryRecordV3]

# --- Config Management ---
class ControlPlaneConfig(BaseModel):
    """
    Configuration distributed from Cloud to Gateway.
    """
    config_version: str
    heartbeat_interval_seconds: int = 30
    discovery_policy: Dict[str, Any]
    spool_max_bytes: int = 104_857_600 # 100MB
