import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
import time

# Add functions dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../functions")))

from firebase_functions import https_fn
from mgmt_api import routes as mgmt_routes

class MockRequest:
    def __init__(self, path, method, json_data, claims=None):
        self.path = path
        self.method = method
        self.json_data = json_data
        self.claims = claims
    
    def get_json(self, silent=True):
        return self.json_data

class MockClaims:
    def __init__(self, role, tenant_id='t1', site_id='s1'):
        self.role = role
        self.tenant_id = tenant_id
        self.site_id = site_id

class TestMgmtAPI(unittest.TestCase):
    
    def test_flow(self):
        # 1. Admin generates code
        req_admin = MockRequest(
            path='/mgmt_api/pairing_codes',
            method='POST',
            json_data={'site_id': 'site_X'},
            claims=MockClaims('admin', 'tenant_X')
        )
        resp_admin = mgmt_routes.dispatch(req_admin)
        self.assertEqual(resp_admin.status_code, 200, f"Generate failed: {resp_admin.response}")
        admin_data = json.loads(resp_admin.response[0])
        code = admin_data['code']
        print(f"Generated Code: {code}")
        
        # 2. Device enrolls with code
        req_enroll = MockRequest(
            path='/mgmt_api/enroll',
            method='POST',
            json_data={'pairing_code': code, 'hardware_info': {}}
        )
        resp_enroll = mgmt_routes.dispatch(req_enroll)
        self.assertEqual(resp_enroll.status_code, 200, "Enroll failed")
        
        enroll_data = json.loads(resp_enroll.response[0])
        self.assertEqual(enroll_data['tenant_id'], 'tenant_X')
        self.assertEqual(enroll_data['site_id'], 'site_X')
        self.assertTrue(enroll_data['gateway_secret'])
        print(f"Device Enrolled: {enroll_data['device_id']}")

        # 3. Reuse code (Should Fail)
        resp_reuse = mgmt_routes.dispatch(req_enroll)
        self.assertEqual(resp_reuse.status_code, 403, "Code reuse should be forbidden")

if __name__ == '__main__':
    unittest.main()
