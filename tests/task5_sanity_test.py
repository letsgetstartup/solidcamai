import asyncio
import json
import os
import sys
import unittest
from datetime import datetime
from simco_common.schemas_v3 import TelemetryRecord, StatusEnum
from simco_common.id import generate_record_id

class TestCloudDataPlaneSanity(unittest.TestCase):
    def test_schema_validation(self):
        print("\n--- Testing Schema Validation ---")
        metrics = {"spindle_load": 45.5, "feed_rate": 1200}
        ts = datetime.utcnow().isoformat()
        
        # 1. Valid Record
        rid = generate_record_id("t1", "s1", "m1", ts, metrics)
        record = TelemetryRecord(
            record_id=rid,
            tenant_id="t1",
            site_id="s1",
            machine_id="m1",
            timestamp=ts,
            status=StatusEnum.ACTIVE,
            metrics=metrics
        )
        print("✅ Pydantic: Valid record generated.")

        # 2. Invalid Record (missing field)
        with self.assertRaises(Exception):
            TelemetryRecord(tenant_id="t1")
        print("✅ Pydantic: Invalid record rejected as expected.")

    def test_idempotency_generation(self):
        print("\n--- Testing Idempotency Generation ---")
        metrics = {"v": 1}
        ts = "2026-01-12T10:00:00"
        id1 = generate_record_id("t", "s", "m", ts, metrics)
        id2 = generate_record_id("t", "s", "m", ts, metrics)
        
        self.assertEqual(id1, id2)
        print("✅ Idempotency: Deterministic IDs match.")

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    unittest.main()
