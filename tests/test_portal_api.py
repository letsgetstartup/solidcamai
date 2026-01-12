import unittest
import json
from functions.main import check_rbac

class TestPortalRBAC(unittest.TestCase):
    def test_tenant_scoping_pass(self):
        class Req: headers = {"X-Dev-Role": "Manager", "X-Dev-Tenant": "tenant_01", "X-Dev-Site": "site_01"}
        allowed, err = check_rbac(Req(), "tenant_01")
        self.assertTrue(allowed)
        self.assertIsNone(err)

    def test_tenant_scoping_fail(self):
        class Req: headers = {"X-Dev-Role": "Manager", "X-Dev-Tenant": "tenant_01", "X-Dev-Site": "site_01"}
        # Accessing tenant_02 with tenant_01 context
        allowed, err = check_rbac(Req(), "tenant_02")
        self.assertFalse(allowed)
        self.assertIn("Cross-tenant breach", err)

    def test_operator_site_scoping_fail(self):
        class Req: headers = {"X-Dev-Role": "Operator", "X-Dev-Tenant": "tenant_01", "X-Dev-Site": "site_01"}
        # Operator restricted to site_01, trying to access site_02
        allowed, err = check_rbac(Req(), "tenant_01", "site_02")
        self.assertFalse(allowed)
        self.assertIn("Cross-site breach", err)

    def test_manager_site_scoping_pass(self):
        class Req: headers = {"X-Dev-Role": "Manager", "X-Dev-Tenant": "tenant_01", "X-Dev-Site": "site_01"}
        # Manager is NOT site-restricted even if site_id doesn't match dev_site
        allowed, err = check_rbac(Req(), "tenant_01", "site_02")
        self.assertTrue(allowed)

if __name__ == "__main__":
    unittest.main()
