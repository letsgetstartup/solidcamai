import unittest
import asyncio
import json
from cloud.processing.bus import LocalBus
from cloud.processing.stream_processor import StreamProcessor
from cloud.processing.notify import dispatcher

class TestHotPathProcessing(unittest.TestCase):
    def setUp(self):
        self.bus = LocalBus()
        self.processor = StreamProcessor()
        # Reset state for fresh test
        self.processor.state_store = {}
        self.processor.event_ids = set()
        dispatcher.notification_log = []
        dispatcher.rate_limits = {}

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_threshold_rule_trigger(self):
        # 1. Setup record that breaches RULE_SPINDLE_LOAD_THRESHOLD (> 90)
        record = {
            "record_id": "rec_001",
            "tenant_id": "tenant_test",
            "site_id": "site_test",
            "machine_id": "CNC-01",
            "timestamp": "2026-01-12T10:00:00Z",
            "status": "RUNNING",
            "metrics": {"spindle_load_pct": 95.0}
        }

        # 2. Process
        self.run_async(self.processor.process_record(record))

        # 3. Verify state updated
        machine_key = "tenant_test:site_test:CNC-01"
        self.assertIn(machine_key, self.processor.state_store)
        self.assertEqual(self.processor.state_store[machine_key]["metrics"]["spindle_load_pct"], 95.0)

        # 4. Verify derived event and notification
        self.assertEqual(len(self.processor.event_ids), 1)
        self.assertEqual(len(dispatcher.notification_log), 1)
        
        last_notif = dispatcher.notification_log[0]
        self.assertEqual(last_notif["machine_id"], "CNC-01")

    def test_idempotency(self):
        record = {
            "record_id": "rec_001",
            "tenant_id": "tenant_test",
            "site_id": "site_test",
            "machine_id": "CNC-01",
            "timestamp": "2026-01-12T10:00:00Z",
            "status": "RUNNING",
            "metrics": {"spindle_load_pct": 95.0}
        }

        # Process twice
        self.run_async(self.processor.process_record(record))
        self.run_async(self.processor.process_record(record))

        # Verify exactly 1 event and 1 notification
        self.assertEqual(len(self.processor.event_ids), 1)
        self.assertEqual(len(dispatcher.notification_log), 1)

    def test_state_change_rule(self):
        # 1. First record (RUNNING) - No alert expected for change rule
        rec1 = {
            "record_id": "rec_1",
            "tenant_id": "t", "site_id": "s", "machine_id": "m1",
            "timestamp": "2026-01-12T10:00:01Z",
            "status": "RUNNING", "metrics": {}
        }
        self.run_async(self.processor.process_record(rec1))
        self.assertEqual(len(self.processor.event_ids), 0)

        # 2. Second record (STOPPED) - Triggers RULE_STATE_CHANGE_STRICT
        rec2 = {
            "record_id": "rec_2",
            "tenant_id": "t", "site_id": "s", "machine_id": "m1",
            "timestamp": "2026-01-12T10:00:02Z",
            "status": "STOPPED", "metrics": {}
        }
        self.run_async(self.processor.process_record(rec2))
        
        # Verify event
        self.assertEqual(len(self.processor.event_ids), 1)
        # Find the event
        found = False
        for machine_key, record in self.processor.state_store.items():
            if record["status"] == "STOPPED":
                found = True
        self.assertTrue(found)

if __name__ == "__main__":
    unittest.main()
