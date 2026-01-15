from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import datetime
import uuid

@dataclass
class Fingerprint:
    """
    Represents the result of a Protocol Handshake Probe.
    Used by the DriverSelector to identify and bin-pack machines to drivers.
    """
    ip: str
    protocol: str
    vendor: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    controller_version: Optional[str] = None
    endpoint: Optional[str] = None  # e.g. "http://192.168.1.5:7878" or "opc.tcp://..."
    confidence: float = 0.0
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class SignalQuality(str, Enum):
    GOOD = "GOOD"
    BAD = "BAD"
    UNCERTAIN = "UNCERTAIN"

@dataclass
class TelemetryPoint:
    """
    A single normalized signal point ready for ingestion.
    """
    name: str # Canonical signal name (e.g. "spindle_speed", "execution_state")
    value: Any
    timestamp: str # ISO8601 UTC
    quality: SignalQuality = SignalQuality.GOOD
    source_timestamp: Optional[str] = None # Original timestamp from device if different

@dataclass
class TelemetryRecord:
    """
    Complete context for a single telemetry event/sample.
    Aligned with Cloud Schema.
    """
    machine_id: str
    timestamp: str
    metrics: Dict[str, Any] # e.g. {"spindle_speed": 1000}
    status: Optional[str] = None
    record_id: Optional[str] = None # Deterministic ID for Idempotency
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    device_id: Optional[str] = None

@dataclass
class TelemetryBatch:
    """
    A transport unit containing multiple records.
    Atomic unit for Buffering and Acknowledgement.
    """
    records: List[TelemetryRecord]
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

@dataclass
class MachineDescriptor:
    """
    Enriched machine metadata stored in the registry.
    """
    machine_id: str
    ip: str
    mac_address: Optional[str] = None
    protocols: List[str] = field(default_factory=list)
    selected_driver_id: Optional[str] = None
    selected_driver_version: Optional[str] = None
    selected_endpoint: Optional[str] = None
    fingerprint: Optional[Fingerprint] = None

@dataclass
class DriverManifest:
    name: str # e.g. "fanuc-focas"
    version: str # e.g. "1.0.0"
    description: str = ""
    protocol: str = "unknown"
    # List of rules. Each rule is a dict of regexes.
    # e.g. [{"vendor": "Fanuc.*", "model": ".*"}]
    match_rules: List[Dict[str, str]] = field(default_factory=list)
    checksum: Optional[str] = None # SHA256 of the driver file

@dataclass
class DriverMatch:
    manifest: DriverManifest
    score: float # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
