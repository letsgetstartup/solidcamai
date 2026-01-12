import unittest
from unittest.mock import patch, MagicMock
from simco_agent.discovery.policy import DiscoveryPolicy
from simco_agent.discovery.passive import discover_passive
from simco_agent.discovery.active import plan_active_scan

class TestDiscoverySuite(unittest.TestCase):
    def test_policy_decisions(self):
        # Manual only
        p = DiscoveryPolicy(mode="manual_only")
        self.assertFalse(p.is_active_allowed())
        self.assertFalse(p.is_passive_allowed())

        # Passive
        p = DiscoveryPolicy(mode="passive")
        self.assertFalse(p.is_active_allowed())
        self.assertTrue(p.is_passive_allowed())

        # Hybrid
        p = DiscoveryPolicy(mode="hybrid")
        self.assertTrue(p.is_active_allowed())
        self.assertTrue(p.is_passive_allowed())

    @patch("subprocess.check_output")
    def test_passive_parsing(self, mock_cmd):
        mock_cmd.return_value = "192.168.1.10 dev eth0 lladdr 00:11:22:33:44:55 REACHABLE"
        res = discover_passive()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["ip"], "192.168.1.10")

    def test_active_scan_plan(self):
        plan = plan_active_scan(subnets=["10.0.0.0/24"], ports=[8193], dry_run=True)
        self.assertIn("10.0.0.0/24", plan["targets"])
        self.assertEqual(plan["ports"], [8193])

if __name__ == "__main__":
    unittest.main()
