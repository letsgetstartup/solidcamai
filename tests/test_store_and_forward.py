import unittest
import os
import shutil
import sqlite3
import time
from simco_agent.core.buffer_manager import BufferManager
from simco_agent.core.uplink_worker import UplinkWorker

class TestStoreAndForward(unittest.TestCase):
    def setUp(self):
        self.test_db = ".tmp_test_buffer.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.bm = BufferManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_idempotency(self):
        payload = {"machine_id": "CNC01", "timestamp": "2026-01-12T10:00:00Z", "spindle_load": 50}
        id1 = self.bm.enqueue(payload)
        id2 = self.bm.enqueue(payload) # Same payload
        
        self.assertEqual(id1, id2)
        
        stats = self.bm.stats()
        self.assertEqual(stats["queued_count"], 1, "Duplicate record was not ignored by idempotency check")

    def test_batch_reserve_and_release(self):
        for i in range(10):
            self.bm.enqueue({"machine_id": f"M{i}", "v": i})
        
        batch = self.bm.reserve_batch(5)
        self.assertEqual(len(batch), 5)
        self.assertEqual(self.bm.stats()["queued_count"], 5)
        
        ids = [item[0] for item in batch]
        self.bm.release(ids)
        self.assertEqual(self.bm.stats()["queued_count"], 10)

if __name__ == "__main__":
    unittest.main()
