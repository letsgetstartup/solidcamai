from typing import Any, Union
from .models import TelemetryPoint, SignalQuality
import datetime

def normalize_execution_state(raw_state: str) -> str:
    """
    Normalizes diverse execution states into canonical SIMCO states:
    ACTIVE, READY, STOPPED, INTERRUPTED, FEED_HOLD, ERROR.
    """
    if not raw_state:
        return "UNKNOWN"
        
    s = raw_state.upper().strip()
    
    mapping = {
        "ACTIVE": "ACTIVE",
        "RUNNING": "ACTIVE",
        "EXECUTING": "ACTIVE",
        "READY": "READY",
        "IDLE": "READY",
        "STOPPED": "STOPPED",
        "PAUSED": "FEED_HOLD",
        "FEED_HOLD": "FEED_HOLD",
        "INTERRUPTED": "INTERRUPTED",
        "EMERGENCY_STOP": "ERROR",
        "ALARM": "ERROR"
    }
    
    return mapping.get(s, "UNKNOWN")

def create_point(name: str, value: Any, quality: SignalQuality = SignalQuality.GOOD) -> TelemetryPoint:
    """Helper to create a TelemetryPoint with current timestamp."""
    return TelemetryPoint(
        name=name,
        value=value,
        timestamp=datetime.datetime.utcnow().isoformat(),
        quality=quality
    )
