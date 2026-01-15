from .schemas_v3 import (
    TelemetryRecordV3, 
    TelemetryBatch, 
    HandshakeResult,
    StatusEnum,
    ProtocolEnum,
    ControllerVendor,
    ControlPlaneConfig
)
from pydantic import ValidationError
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def adapt_v2_record(record: dict, gateway_id: str) -> TelemetryRecordV3:
    """
    Adapts a legacy v2 or loose dictionary record to TelemetryRecordV3.
    Fills missing fields with defaults or derived values.
    """
    
    # 1. Ensure IDs
    if "record_id" not in record:
        record["record_id"] = str(uuid.uuid4())
        
    # 2. Add Gateway ID if missing
    if "gateway_id" not in record:
        record["gateway_id"] = gateway_id
        
    # 3. Timestamp normalization
    if "timestamp" in record and "ts_utc" not in record:
        record["ts_utc"] = record["timestamp"]
        
    # 4. Default Driver ID
    if "driver_id" not in record:
        record["driver_id"] = "legacy_adapter"

    # 5. Quality
    if "quality" not in record:
        record["quality"] = None

    try:
        return TelemetryRecordV3(**record)
    except ValidationError as e:
        logger.error(f"Failed to adapt v2 record: {e} - Data: {record}")
        raise
