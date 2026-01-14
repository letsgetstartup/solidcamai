import asyncio
import unittest
import os
import time
import json
import logging
import shutil
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.core.uplink_worker import UplinkWorker
from simco_agent.core.buffer_manager import BufferManager
from simco_agent.drivers.common.models import TelemetryBatch, TelemetryRecord

class TestReliability(unittest.TestCase):
    
    def setUp(self):
        self.test_db = "/tmp/test_buffer.db"
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        # Use short interval for testing
        with patch.dict(os.environ, {"UPLOAD_INTERVAL_SECONDS": "0.1"}):
            self.bm = BufferManager(db_path=self.test_db)
            self.worker = UplinkWorker(buffer_manager=self.bm)
            self.worker.interval = 0.1
            self.worker.ingest_url = "http://mock-cloud/ingest"

    def tearDown(self):
        self.worker.stop()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_offline_buffering_and_recovery(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 1. Mock Request to Fail (Offline)
        post_mock = MagicMock()
        post_mock.side_effect = Exception("Network Down")
        
        # 2. Inject Batches
        # Construct Dummy Batch
        from simco_agent.drivers.common.models import TelemetryBatch
        from uuid import uuid4
        batch1 = TelemetryBatch(uuid=str(uuid4()), records=[]) # Empty records ok for transport test
        batch2 = TelemetryBatch(uuid=str(uuid4()), records=[])
        
        self.worker.submit_batch(batch1)
        self.worker.submit_batch(batch2)
        
        # Verify Buffer has 2
        self.assertEqual(self.bm.count(), 2)
        print("Buffer Fill: SUCCESS")
        
        # 3. Run Worker with Failing Network
        logging.basicConfig(level=logging.INFO)
        async def run_failure_scenario():
            original_sleep = asyncio.sleep
            # Patch sleep to avoid waiting for backoff
            with patch('requests.post', post_mock), \
                 patch('simco_agent.core.uplink_worker.asyncio.sleep', new_callable=MagicMock) as mock_sleep:
                
                # Make sleep allow context switch but be instant
                mock_sleep.side_effect = lambda x: original_sleep(0.001)

                # Start worker
                task = loop.create_task(self.worker.run())
                
                # Let it run a few cycles
                await asyncio.sleep(0.5)
                
                # Verify Buffer still 2 (because failing)
                self.assertEqual(self.bm.count(), 2)
                # Verify attempts made
                self.assertGreaterEqual(post_mock.call_count, 1)
                
                print("Offline Persistence: SUCCESS")
                
                # 4. Recover Network (Success)
                post_mock.side_effect = None
                post_mock.return_value.status_code = 200
                
                # Reset backoff count if needed, but with mocked sleep it shouldn't matter much
                self.worker.backoff_count = 0
                
                # Drain - Poll until empty or timeout
                start_t = time.time()
                while time.time() - start_t < 2.0:
                    if self.bm.count() == 0:
                        break
                    await asyncio.sleep(0.1)
                
                # Verify Buffer Drained
                self.assertEqual(self.bm.count(), 0, "Buffer failed to drain")
                print("Recovery Drain: SUCCESS")
                
                # Verify Headers
                call_args = post_mock.call_args
                kwargs = call_args[1]
                headers = kwargs.get('headers', {})
                self.assertIn('X-Idempotency-Key', headers)
                # Should be batch2.uuid because batch1 was sent/acked, then batch2 sent.
                # Since we check the LAST call.
                if self.bm.count() == 0:
                   self.assertEqual(headers['X-Idempotency-Key'], batch2.uuid)

                # Let's cancel worker
                self.worker.stop()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        from unittest.mock import AsyncMock
        loop.run_until_complete(run_failure_scenario())
        loop.close()

if __name__ == '__main__':
    unittest.main()
