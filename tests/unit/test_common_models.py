import pytest
from simco_agent.drivers.common.models import Fingerprint, TelemetryPoint, SignalQuality
from simco_agent.drivers.common.errors import DriverError, DriverErrorCode, HandshakeError
from simco_agent.drivers.common.normalize import normalize_execution_state, create_point
import json
from dataclasses import asdict

def test_fingerprint_creation():
    fp = Fingerprint(
        ip="192.168.1.100",
        protocol="mtconnect",
        vendor="Haas",
        endpoint="http://192.168.1.100:7878"
    )
    assert fp.ip == "192.168.1.100"
    assert fp.confidence == 0.0
    assert fp.evidence == {}
    assert fp.timestamp is not None

def test_telemetry_point_structure():
    tp = TelemetryPoint(
        name="spindle_speed",
        value=1200.5,
        timestamp="2026-01-01T12:00:00Z"
    )
    assert tp.quality == SignalQuality.GOOD
    assert tp.value == 1200.5

def test_execution_state_normalization():
    assert normalize_execution_state("ACTIVE") == "ACTIVE"
    assert normalize_execution_state("running") == "ACTIVE"
    assert normalize_execution_state("PAUSED") == "FEED_HOLD"
    assert normalize_execution_state("emergency_stop") == "ERROR"
    assert normalize_execution_state("StrangeState") == "UNKNOWN"
    assert normalize_execution_state(None) == "UNKNOWN"

def test_helper_create_point():
    tp = create_point("temp", 100)
    assert tp.name == "temp"
    assert tp.value == 100
    assert tp.timestamp is not None
    assert tp.quality == SignalQuality.GOOD

def test_driver_error():
    err = DriverError("Auth failed", code=DriverErrorCode.AUTH_FAILED)
    assert err.code == DriverErrorCode.AUTH_FAILED
    assert str(err) == "Auth failed"
    
    with pytest.raises(HandshakeError):
        raise HandshakeError("Handshake failed")
