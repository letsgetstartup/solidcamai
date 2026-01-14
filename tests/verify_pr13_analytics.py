import unittest
from unittest.mock import MagicMock, patch
import json
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock firebase_functions and google.cloud before importing main
class FakeResponse:
    def __init__(self, response, status=200, headers=None, mimetype=None):
        self.response = [response] # Mimic Werkzeug response iterator
        self.status_code = status
        self.headers = headers or {}
        self.mimetype = mimetype

sys.modules["firebase_functions"] = MagicMock()
sys.modules["firebase_functions"].https_fn.Response = FakeResponse
# Mock decorator to return function as is
sys.modules["firebase_functions"].https_fn.on_request = lambda **kwargs: (lambda func: func)

sys.modules["firebase_admin"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["functions.portal_api"] = MagicMock()
sys.modules["functions.mgmt_api"] = MagicMock()
sys.modules["functions.ingest_api"] = MagicMock()
sys.modules["admin_api"] = MagicMock()
sys.modules["auth"] = MagicMock()
sys.modules["auth.middleware"] = MagicMock()
sys.modules["auth.middleware"].require_auth = lambda f: f
sys.modules["cloud.processing.bus"] = MagicMock()
sys.modules["cloud.processing.stream_processor"] = MagicMock()

try:
    from functions.main import metrics_history
except ImportError as e:
    print(f"Skipping import main: {e}")
    import traceback
    traceback.print_exc()

class TestAnalytics(unittest.TestCase):
    
    def test_metrics_history(self):
        print("Testing Metrics History API...")
        
        # Mock Request
        req = MagicMock()
        req.method = "GET"
        req.args = {
            "machine_id": "m1",
            "start": "2024-01-01T00:00:00Z",
            "end": "2024-01-01T23:59:59Z",
            "tenant_id": "t1" # Injected via args for test simplicity or mock validate_auth
        }
        
        # Mock validate_auth to allow tenant_id
        with patch('functions.main.validate_auth') as mock_auth, \
             patch('functions.main.get_bq_client') as mock_bq:
            
            mock_auth.return_value = {"tenant_id": "t1"}
            
            # Mock BQ Result
            mock_row1 = {"hour_bucket": "2024-01-01T10:00:00Z", "minutes_active": 45, "minutes_idle": 15, "minutes_alarm": 0}
            mock_row2 = {"hour_bucket": "2024-01-01T11:00:00Z", "minutes_active": 60, "minutes_idle": 0, "minutes_alarm": 0}
            
            mock_job = MagicMock()
            mock_job.result.return_value = [mock_row1, mock_row2]
            mock_bq.return_value.query.return_value = mock_job
            
            # Execute
            res = metrics_history(req)
            
            # Verify
            body = json.loads(res.response[0])
            print(f"  Got Response: {json.dumps(body)}")
            
            self.assertEqual(len(body), 2)
            self.assertEqual(body[0]["minutes_active"], 45)
            self.assertEqual(body[1]["minutes_active"], 60)
            
            # Verify Query Parameters
            call_args = mock_bq.return_value.query.call_args
            # Check if query text contains view name
            self.assertIn("hourly_machine_stats", call_args[0][0])
            print("  Query Confirmed.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL)
    unittest.main()
