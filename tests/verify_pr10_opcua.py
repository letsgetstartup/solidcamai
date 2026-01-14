import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.drivers.loader import SecureDriverLoader
from simco_agent.discovery.selection import DriverSelector

class TestSiemensDriverMock(unittest.TestCase):
    
    def test_mocked_client_interaction(self):
        # 0. Setup Loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 1. Load Driver Securely
            selector = DriverSelector()
            manifest = next((m for m in selector.manifests if m.name == "siemens_opcua"), None)
            self.assertIsNotNone(manifest)
            print(f"Checksum: {manifest.checksum}")
            
            loader = SecureDriverLoader()
            module = loader.load_driver(manifest)
            
            # 2. Patch the Client inside the loaded module
            mock_client_cls = MagicMock()
            mock_client_instance = MagicMock()
            mock_client_cls.return_value = mock_client_instance
            
            # connect() is async - use loop.create_future()
            f = loop.create_future()
            f.set_result(None)
            mock_client_instance.connect.return_value = f
            
            # Mock Nodes
            def get_node_side_effect(node_id):
                node = MagicMock()
                val_future = loop.create_future()
                
                if "speed" in node_id and "speedOvr" not in node_id:
                    val_future.set_result(12000.0)
                elif "feedRate" in node_id:
                    val_future.set_result(500.0)
                elif "progStatus" in node_id:
                    val_future.set_result("RUNNING")
                else:
                     val_future.set_result(None)
                
                node.read_value.return_value = val_future
                return node
                
            mock_client_instance.get_node.side_effect = get_node_side_effect
            
            # Inject Mock
            module.Client = mock_client_cls
            
            # 3. Instantiate Driver
            DriverClass = getattr(module, "SiemensOPCUADriver")
            driver = DriverClass(config={"ip": "1.2.3.4"})
            
            # 4. Run Connect
            connected = loop.run_until_complete(driver.connect())
            self.assertTrue(connected)
            mock_client_instance.connect.assert_called_once()
            print("Mock Connect: SUCCESS")
            
            # 5. Collect Metrics
            points = loop.run_until_complete(driver.collect_metrics())
            
            vals = {p.name: p.value for p in points}
            print(f"Collected: {vals}")
            
            # Verify Mappings
            self.assertEqual(vals["spindle_speed"], 12000.0)
            self.assertEqual(vals["feed_rate"], 500.0)
            self.assertEqual(vals["execution_state"], "RUNNING")
            
            print("Data Logic Verification: SUCCESS")
            
        finally:
            loop.close()

if __name__ == '__main__':
    unittest.main()
