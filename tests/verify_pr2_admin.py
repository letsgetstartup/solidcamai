import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add functions dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../functions")))

from firebase_functions import https_fn
# We need to mock firebase_admin before importing routes potentially
with patch('firebase_admin.initialize_app'):
    from admin_api import routes as admin_routes

# Mock Request Object
class MockRequest:
    def __init__(self, json_data=None, method='POST', path='/admin_api/v1/invites'):
        self.json_data = json_data or {}
        self.method = method
        self.path = path
        self.claims = None

    def get_json(self, silent=True):
        return self.json_data

class MockClaims:
    def __init__(self, role='viewer', tenant_id='t1'):
        self.role = role
        self.tenant_id = tenant_id

class TestAdminAPI(unittest.TestCase):

    @patch('admin_api.routes.auth')
    @patch('admin_api.routes.set_custom_claims')
    def test_invite_success(self, mock_set_claims, mock_auth):
        # Setup
        req = MockRequest(json_data={'email': 'new@test.com', 'role': 'operator', 'site_id': 's1'})
        req.claims = MockClaims(role='admin', tenant_id='tenant_A')
        
        # Mock Auth User
        mock_user = MagicMock()
        mock_user.uid = 'new_uid'
        mock_auth.get_user_by_email.side_effect = Exception("UserNotFoundError") # Simulate not found
        # Actually auth.UserNotFoundError is a class, we need to mock raising it or just let create_user run
        # Let's mock create_user
        mock_auth.create_user.return_value = mock_user
        
        # Execute
        # We need to bypass the exception check for UserNotFoundError which is tricky to mock perfectly without importing the real exception class
        # So we'll patch get_user_by_email to RAISE the real exception if we can import it, or just use a generic one if the code catches Exception (it doesn't, it catches UserNotFoundError)
        
        # Easier path: Mock get_user_by_email to return a user (Update flow)
        mock_auth.get_user_by_email.return_value = mock_user
        mock_auth.UserNotFoundError = Exception
        
        resp = admin_routes.dispatch(req)
        
        # Verify
        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.data)
        self.assertEqual(resp_data['uid'], 'new_uid')
        
        # Verify set_custom_claims called with correct tenant from admin context
        mock_set_claims.assert_called_with('new_uid', 'tenant_A', 's1', 'operator')

    def test_forbidden_access(self):
        req = MockRequest()
        req.claims = MockClaims(role='viewer') # Not admin
        
        resp = admin_routes.dispatch(req)
        
        self.assertEqual(resp.status_code, 403)

if __name__ == '__main__':
    unittest.main()
