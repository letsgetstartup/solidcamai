import unittest
from unittest.mock import MagicMock, patch
import json
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock firebase_functions and google.cloud before importing main
sys.modules["firebase_functions"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["functions.portal_api"] = MagicMock()
sys.modules["functions.mgmt_api"] = MagicMock()
sys.modules["functions.ingest_api"] = MagicMock()
sys.modules["admin_api"] = MagicMock()
sys.modules["auth"] = MagicMock()
sys.modules["auth.middleware"] = MagicMock()
# Mock decorator to return function as is
sys.modules["auth.middleware"].require_auth = lambda f: f

sys.modules["cloud.processing.bus"] = MagicMock()
sys.modules["cloud.processing.stream_processor"] = MagicMock()

# Mocking Response object
class FakeResponse:
    def __init__(self, response, status=200, headers=None, mimetype=None):
        self.response = [response] # Mimic Werkzeug response iterator
        self.status_code = status
        self.headers = headers or {}
        self.mimetype = mimetype

sys.modules["firebase_functions"].https_fn.Response = FakeResponse
# Mock decorator to return function as is
sys.modules["firebase_functions"].https_fn.on_request = lambda **kwargs: (lambda func: func)

try:
    from functions.main import pair_init, pair_confirm, pair_token, resolve_mobile_context, _pairing_store
except ImportError as e:
    print(f"Skipping import main: {e}")
    import traceback
    traceback.print_exc()
    pass

class TestAuthFlows(unittest.TestCase):
    
    def setUp(self):
        # Clear store
        _pairing_store.clear()
        
    def mock_req(self, method="POST", json_data=None, headers=None, args=None):
        req = MagicMock()
        req.method = method
        req.get_json.return_value = json_data or {}
        req.headers = headers or {}
        req.args = args or {}
        return req

    def test_pairing_flow(self):
        print("Testing TV Pairing Flow...")
        
        # 1. TV Init
        req = self.mock_req(json_data={"fingerprint": "tv-1"})
        res = pair_init(req)
        # FakeResponse puts body in list
        body_str = res.response[0]
        body = json.loads(body_str)
        code = body["code"]
        print(f"  Got Code: {code}")
        self.assertEqual(len(code), 6)
        
        # 2. TV Poll (Before Confirm) -> Pending
        req = self.mock_req(json_data={"code": code})
        res = pair_token(req)
        body = json.loads(res.response[0])
        self.assertEqual(body["status"], "PENDING")
        print("  Poll Status: PENDING (Correct)")
        
        # 3. Admin Confirm
        # Validate_auth path needs to be functions.main.validate_auth because we imported pair_confirm from there
        # But actually, pair_confirm uses validate_auth which is imported in main.py
        # If we patch 'functions.main.validate_auth', it should work.
        with patch('functions.main.validate_auth') as mock_auth:
            mock_auth.return_value = {"role": "Admin", "user_id": "admin_1"}
            
            req = self.mock_req(json_data={"code": code, "tenant_id": "t1", "site_id": "s1"})
            res = pair_confirm(req)
            body = json.loads(res.response[0])
            self.assertEqual(body["status"], "SUCCESS")
            print("  Admin Confirm: SUCCESS")
            
        # 4. TV Poll (After Confirm) -> Success
        req = self.mock_req(json_data={"code": code})
        res = pair_token(req)
        body = json.loads(res.response[0])
        self.assertEqual(body["status"], "SUCCESS")
        self.assertTrue(body["token"].startswith("display_"))
        print(f"  Received Token: {body['token']}")
        
    def test_mobile_context(self):
        print("Testing Mobile QR Resolve...")
        # Mock BigQuery Client
        with patch('functions.main.get_bq_client') as mock_bq:
            mock_client = MagicMock()
            mock_bq.return_value = mock_client
            
            # Mock Result
            mock_row = MagicMock()
            mock_row.tenant_id = "t_mob"
            mock_row.site_id = "s_mob"
            mock_row.vendor = "Fanuc"
            
            mock_job = MagicMock()
            mock_job.result.return_value = [mock_row]
            mock_client.query.return_value = mock_job
            
            import base64
            token = base64.urlsafe_b64encode(b"machine_123").decode()
            
            req = self.mock_req(method="GET", args={"token": token})
            res = resolve_mobile_context(req)
            body = json.loads(res.response[0])
            
            self.assertEqual(body["machine_id"], "machine_123")
            self.assertEqual(body["tenant_id"], "t_mob")
            print("  Mobile Context Resolved: machine_123 -> t_mob")

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL) # Silence logs
    unittest.main()
