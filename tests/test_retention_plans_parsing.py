import unittest
import yaml
import os
from cloud.data_lifecycle.enforce_retention import load_plans

class TestRetentionPlans(unittest.TestCase):
    def test_load_standard_plan(self):
        # In a real test, use a temp file. Here we test the actual artifact.
        path = "cloud/data_lifecycle/retention_plans.yaml"
        plans = load_plans(path)
        self.assertIn("retention_plans", plans)
        self.assertEqual(plans["retention_plans"]["standard"]["telemetry_raw"], 90)

    def test_tenant_overrides(self):
        path = "cloud/data_lifecycle/retention_plans.yaml"
        plans = load_plans(path)
        self.assertEqual(plans["tenant_overrides"]["tenant_demo"], "pilot")

if __name__ == "__main__":
    unittest.main()
