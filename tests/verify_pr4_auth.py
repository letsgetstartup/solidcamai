import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add project root AND functions dir to path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "functions"))

from firebase_functions import https_fn
from functions.mgmt_api import routes as mgmt_routes
import firebase_admin
from firebase_admin import auth

# Need to patch firebase_admin before importing main
with patch('firebase_admin.initialize_app'):
    from functions.main import ingest_telemetry

class MockRequest:
    def __init__(self, path, method, json_data, headers={}):
        self.path = path
        self.method = method
        self.json_data = json_data
        self.headers = headers
    
    def get_json(self, silent=True):
        return self.json_data

class TestGatewayAuth(unittest.TestCase):
    
    @patch('auth.middleware.auth.verify_id_token')
    def test_gateway_auth_flow(self, mock_verify_user):
        # 1. Enroll to get Token
        # Need to seed a code first or mock PAIRING_CODES_DB
        from functions.mgmt_api.routes import PAIRING_CODES_DB
        PAIRING_CODES_DB['TESTCODE'] = {"tenant_id": "t1", "site_id": "s1", "expires_at": 9999999999}
        
        req_enroll = MockRequest('/enroll', 'POST', {'pairing_code': 'TESTCODE'})
        resp_enroll = mgmt_routes.dispatch(req_enroll)
        self.assertEqual(resp_enroll.status_code, 200)
        
        data = json.loads(resp_enroll.response[0])
        token = data['gateway_token']
        print(f"Issued Token: {token[:20]}...")
        
        # 2. Try Ingest with Token
        # Mock verify_id_token to fail with REAL exception so middleware catches it
        mock_verify_user.side_effect = auth.InvalidIdTokenError("Simulated Invalid Token")
        
        req_ingest = MockRequest('/ingest', 'POST', {'records': []}, headers={'Authorization': f'Bearer {token}'})
        
        # We need to spy on 'simco_common.schemas_v3.TelemetryBatch' validation potentially 
        # or just expect 400 (No JSON provided handled, or schema check logic).
        # Actually ingest_api checks json first.
        # If schema fails, it might return error, but middleware should pass us through.
        
        # Run ingest_telemetry
        # Warning: ingest_telemetry imports from `simco_common.schemas_v3`. Ensure that exists or mock it?
        # Assuming simco_common is in pythonpath (main.py does sys.path.append(..)).
        
        resp_ingest = ingest_telemetry(req_ingest)
        
        # If Auth worked, we should get 400 (No JSON provided/Schema invalid) or 200.
        # If Auth failed, we get 401.
        self.assertNotEqual(resp_ingest.status_code, 401, "Should pass auth check")
        print(f"Ingest Status with Token: {resp_ingest.status_code}")

    @patch('auth.middleware.auth.verify_id_token')
    def test_missing_token(self, mock_verify):
        mock_verify.side_effect = Exception("Invalid") # Fail user check
        
        req_ingest = MockRequest('/ingest', 'POST', {}, headers={})
        resp_ingest = ingest_telemetry(req_ingest)
        
        self.assertEqual(resp_ingest.status_code, 401)
        print("Ingest with No Token: 401 OK")

if __name__ == '__main__':
    unittest.main()
