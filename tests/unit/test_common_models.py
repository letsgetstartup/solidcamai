import pytest
from simco_common.models import adapt_v2_record
from simco_common.schemas_v3 import TelemetryRecordV3

def test_adapt_v2_record_success():
    legacy_data = {
        "tenant_id": "t1",
        "site_id": "s1",
        "machine_id": "m1",
        "timestamp": "2024-01-01T12:00:00Z",
        "metrics": {"rpm": 1200}
    }
    
    record = adapt_v2_record(legacy_data, gateway_id="gw_legacy")
    
    assert isinstance(record, TelemetryRecordV3)
    assert record.gateway_id == "gw_legacy"
    assert record.metrics["rpm"] == 1200
    assert record.driver_id == "legacy_adapter"
    assert record.record_id is not None # Generated UUID
    assert record.ts_utc == "2024-01-01T12:00:00Z"

def test_adapt_v2_record_preserves_existing():
    data = {
        "record_id": "fixed-id",
        "tenant_id": "t1",
        "site_id": "s1",
        "gateway_id": "gw_original",
        "machine_id": "m1",
        "driver_id": "real_driver",
        "ts_utc": "2024-01-01T12:00:00Z",
        "metrics": {}
    }
    
    record = adapt_v2_record(data, gateway_id="gw_ignoted")
    
    assert record.gateway_id == "gw_original" # Should not be overwritten
    assert record.driver_id == "real_driver"
    assert record.record_id == "fixed-id"
