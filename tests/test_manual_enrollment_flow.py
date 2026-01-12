import unittest
import json
import os
from unittest.mock import MagicMock
from simco_agent.core.config_manager import ConfigManager
from simco_agent.core.device_state import DeviceState

class TestManualEnrollment(unittest.TestCase):
    def setUp(self):
        self.registry_path = "machine_registry.json"
        if os.path.exists(self.registry_path):
            os.remove(self.registry_path)
        
        self.state = MagicMock(spec=DeviceState)
        self.mgr = ConfigManager(self.state)

    def test_apply_manual_enrollment(self):
        new_config = {
            "pending_manual_enrollments": [
                {"machine_ip": "192.168.1.50", "vendor": "Haas", "machine_id": "HAAS-01"}
            ]
        }
        
        # Apply config delta
        self.mgr._apply_config(new_config, version=2)
        
        # Verify registry entry
        self.assertTrue(os.path.exists(self.registry_path))
        with open(self.registry_path, "r") as f:
            registry = json.load(f)
            self.assertIn("192.168.1.50", registry)
            self.assertEqual(registry["192.168.1.50"]["machine_id"], "HAAS-01")
            self.assertEqual(registry["192.168.1.50"]["status"], "MANUAL_ENROLLED")

    def tearDown(self):
        if os.path.exists(self.registry_path):
            os.remove(self.registry_path)

if __name__ == "__main__":
    unittest.main()
