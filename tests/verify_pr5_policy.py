import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
import json
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.core.config_manager import ConfigManager
from simco_agent.discovery.orchestrator import DiscoveryOrchestrator
from simco_agent.core.device_state import DeviceState

class TestDynamicPolicy(unittest.TestCase):
    
    @patch('simco_agent.core.config_manager.requests.post')
    def test_apply_cloud_policy(self, mock_post):
        # 1. Setup Mock Response from Cloud
        cloud_config = {
            "config_version": 101,
            "changed": True,
            "config": {
                "scan_interval": 60,
                "discovery": {
                    "enabled": True,
                    "subnets": ["10.0.0.0/24"],
                    "protocols": ["mtconnect"]
                }
            }
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = cloud_config
        mock_post.return_value = mock_resp
        
        # 2. Init ConfigManager
        state = DeviceState()
        state.update(device_id="dev1", is_enrolled=True, gateway_token="test_token")
        
        cm = ConfigManager(state=state)
        
        # 3. Validates Internal Orchestrator access (Mocking DiscoveryOrchestrator to inspect calls)
        with patch('simco_agent.core.config_manager.DiscoveryOrchestrator') as MockOrch:
            orch_instance = MockOrch.return_value
            
            # Run Poll
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(cm._poll_config())
            
            # 4. Verify Update Policy Called
            orch_instance.update_policy.assert_called_once()
            call_args = orch_instance.update_policy.call_args[0][0]
            
            self.assertEqual(call_args['discovery']['subnets'], ["10.0.0.0/24"])
            print("ConfigManager correctly passed policy to Orchestrator.")
            
    def test_orchestrator_mapping(self):
        # Test the Orchestrator's internal mapping logic (real object)
        orch = DiscoveryOrchestrator()
        
        cloud_cfg = {
            "discovery": {
                "subnets": ["10.10.10.0/24"],
                "protocols": ["mtconnect", "opc_ua"]
            }
        }
        
        orch.update_policy(cloud_cfg)
        
        # Verify Subnet Mapping
        self.assertEqual(orch.policy.allowed_subnets, ["10.10.10.0/24"])
        print(f"Subnets Mapped: {orch.policy.allowed_subnets}")
        
        # Verify Protocol Filtering
        # mtconnect(7878) and opc_ua(4840) should be present
        self.assertIn("mtconnect", orch.policy.port_probes)
        self.assertIn("opc_ua", orch.policy.port_probes)
        self.assertNotIn("modbus", orch.policy.port_probes)
        print(f"Probes Mapped: {orch.policy.port_probes.keys()}")

if __name__ == '__main__':
    unittest.main()
