import pytest
from simco_common.schemas_v3 import (
    TelemetryRecordV3, 
    HandshakeResult, 
    ControllerVendor, 
    ProtocolEnum
)
from pydantic import ValidationError

def test_telemetry_record_valid():
    record = TelemetryRecordV3(
        record_id="uuid-123",
        ts_utc="2024-01-01T12:00:00Z",
        tenant_id="tenant_1",
        site_id="site_1",
        gateway_id="gw_1",
        machine_id="m_1",
        driver_id="test_driver",
        metrics={"execution": "ACTIVE", "rpm": 1000}
    )
    assert record.tenant_id == "tenant_1"
    assert record.metrics["rpm"] == 1000

def test_telemetry_record_invalid_timestamp():
    with pytest.raises(ValidationError):
        TelemetryRecordV3(
            record_id="uuid-123",
            ts_utc="invalid-time",
            tenant_id="t1",
            site_id="s1",
            gateway_id="g1",
            machine_id="m1",
            driver_id="d1"
        )

def test_handshake_result():
    res = HandshakeResult(
        controller_vendor=ControllerVendor.SIEMENS,
        controller_model="828D",
        protocol=ProtocolEnum.OPCUA,
        endpoint={"url": "opc.tcp://localhost"},
        fingerprint_sha256="hex123",
        confidence=0.95
    )
    assert res.controller_vendor == "SIEMENS"
    assert res.confidence == 0.95
