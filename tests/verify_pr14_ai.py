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
        self.response = [response] 
        self.status_code = status
        self.headers = headers or {}
        self.mimetype = mimetype

sys.modules["firebase_functions"] = MagicMock()
sys.modules["firebase_functions"].https_fn.Response = FakeResponse
sys.modules["firebase_functions"].https_fn.on_request = lambda **kwargs: (lambda func: func)

sys.modules["firebase_admin"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()

# Mock other modules
for m in ["functions.portal_api", "functions.mgmt_api", "functions.ingest_api", "admin_api", "auth", "auth.middleware", "cloud.processing.bus", "cloud.processing.stream_processor"]:
    sys.modules[m] = MagicMock()
    if "auth" in m:
         sys.modules[m].require_auth = lambda f: f

try:
    from functions.main import ask
except ImportError as e:
    print(f"Skipping import main: {e}")
    import traceback
    traceback.print_exc()

class TestAIInvestigator(unittest.TestCase):
    
    def mock_req(self, json_data):
        req = MagicMock()
        req.method = "POST"
        req.get_json.return_value = json_data
        req.headers = {"X-Tenant-ID": "test_tenant"}
        return req

    def test_intent_orders(self):
        print("Testing Intent: ORDERS...")
        with patch('functions.main.get_bq_client') as mock_bq:
            # Mock BQ Result
            mock_row = {"order_id": "ORD-123", "product_id": "P1", "status": "Pending", "quantity": 100, "due_date": "2024-01-01"}
            mock_bq.return_value.query.return_value.result.return_value = [mock_row]
            
            res = ask(self.mock_req({"question": "Show me active orders"}))
            body = json.loads(res.response[0])
            
            self.assertIn("found 1 active orders", body["answer"].lower())
            self.assertEqual(body["visualization"]["type"], "bar")
            self.assertIn("raw_erp_orders", mock_bq.return_value.query.call_args[0][0])
            print("  Orders Intent: PASS")

    def test_intent_telemetry(self):
        print("Testing Intent: TELEMETRY...")
        with patch('functions.main.get_bq_client') as mock_bq:
            # Mock BQ Result
            mock_row = {"machine_id": "M1", "metric": "spindle_load", "value": 75.5, "timestamp": "2024-01-01T12:00:00"}
            mock_bq.return_value.query.return_value.result.return_value = [mock_row]
            
            res = ask(self.mock_req({"question": "Check spindle load for M1"}))
            body = json.loads(res.response[0])
            
            self.assertIn("latest telemetry loaded", body["answer"].lower())
            self.assertEqual(body["visualization"]["type"], "bar") # It defaults to bar for telemetry list in my code? check line 1522: viz_type="line", line 1592: if line -> type=bar? Ah, actually code says if line & metric -> set type=bar (simplified).
            
            self.assertIn("raw_telemetry", mock_bq.return_value.query.call_args[0][0])
            print("  Telemetry Intent: PASS")
            
    def test_intent_events(self):
        print("Testing Intent: EVENTS (Default)...")
        with patch('functions.main.get_bq_client') as mock_bq:
            # Mock BQ Result
            mock_row = {"machine_id": "M1", "type": "ALARM", "event_count": 5}
            mock_bq.return_value.query.return_value.result.return_value = [mock_row]
            
            res = ask(self.mock_req({"question": "Why did it stop? Show alarms."}))
            body = json.loads(res.response[0])
            
            self.assertIn("top machine for events", body["answer"].lower())
            self.assertIn("raw_events", mock_bq.return_value.query.call_args[0][0])
            print("  Events Intent: PASS")

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL)
    unittest.main()
