import hashlib
import json
from typing import Dict, Any

def generate_record_id(tenant_id: str, site_id: str, machine_id: str, timestamp: str, core_metrics: Dict[str, Any]) -> str:
    """Generates a deterministic SHA-256 ID for a telemetry record."""
    # Stable subset of metrics for hashing
    stable_metrics = {k: core_metrics[k] for k in sorted(core_metrics.keys()) if isinstance(core_metrics[k], (int, float, str, bool))}
    
    raw_str = f"{tenant_id}|{site_id}|{machine_id}|{timestamp}|{json.dumps(stable_metrics, sort_keys=True)}"
    return hashlib.sha256(raw_str.encode()).hexdigest()

def generate_event_id(tenant_id: str, site_id: str, machine_id: str, timestamp: str, event_type: str) -> str:
    """Generates a deterministic SHA-256 ID for an event record."""
    raw_str = f"{tenant_id}|{site_id}|{machine_id}|{timestamp}|{event_type}"
    return hashlib.sha256(raw_str.encode()).hexdigest()
