import unittest
from dataclasses import asdict
import json
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.discovery.fingerprint_hasher import generate_machine_id
from simco_agent.discovery.selection import DriverSelector
from simco_agent.discovery.orchestrator import DiscoveryOrchestrator
from simco_agent.drivers.common.models import Fingerprint, DriverManifest
from simco_agent.core.registry import save_registry, load_registry

TEST_REGISTRY = "/tmp/test_registry_pr7.json"

class TestRegistryAndSelection(unittest.TestCase):
    
    def setUp(self):
        # Reset registry
        if os.path.exists(TEST_REGISTRY):
            os.remove(TEST_REGISTRY)

    def test_hashing_stability(self):
        fp1 = Fingerprint(ip="192.168.1.5", protocol="mtconnect", vendor="Haas", model="VF2")
        fp2 = Fingerprint(ip="192.168.1.5", protocol="mtconnect", vendor="Haas", model="VF2")
        fp3 = Fingerprint(ip="192.6.6.6", protocol="mtconnect")
        
        h1 = generate_machine_id(fp1)
        h2 = generate_machine_id(fp2)
        h3 = generate_machine_id(fp3)
        
        self.assertEqual(h1, h2, "Hash should be deterministic")
        self.assertNotEqual(h1, h3, "Different machines should have different hashes")
        print(f"Machine Hash: {h1}")

    def test_driver_selection(self):
        selector = DriverSelector()
        
        # Case 1: Haas Match
        fp = Fingerprint(ip="1.1.1.1", protocol="mtconnect", vendor="Haas AutomationInc", model="VF-2SS")
        match = selector.select_driver(fp)
        
        self.assertIsNotNone(match)
        self.assertEqual(match.manifest.name, "haas-mtconnect")
        self.assertTrue(match.score > 0.5)
        print(f"Selected: {match.manifest.name} Score: {match.score}")
        
        # Case 2: Siemens Match
        fp_siemens = Fingerprint(ip="1.1.1.2", protocol="opc_ua", vendor="Siemens AG")
        match_s = selector.select_driver(fp_siemens)
        self.assertEqual(match_s.manifest.name, "siemens-opcua")

    def test_orchestrator_integration(self):
        # 1. Setup minimal registry with a discovered machine
        init_data = [{
            "machine_id": "192.168.1.100", # Temporary ID
            "ip": "192.168.1.100",
            "status": "DISCOVERED"
        }]
        save_registry(init_data, TEST_REGISTRY)
        
        # 2. Run Orchestrator Save
        orch = DiscoveryOrchestrator(registry_path=TEST_REGISTRY)
        
        fp = Fingerprint(
            ip="192.168.1.100", 
            protocol="mtconnect", 
            vendor="Haas", 
            model="VF-4",
            confidence=0.9
        )
        
        orch.save_fingerprints([fp])
        
        # 3. Verify Persistence
        data = load_registry(TEST_REGISTRY)
        entry = data[0]
        
        self.assertEqual(entry["status"], "READY_TO_ENROLL")
        self.assertEqual(entry["driver_id"], "haas-mtconnect")
        self.assertIn("machine_hash", entry["metadata"])
        
        # Verify ID Promotion
        # Since source != manual_portal, machine_id should update to hash
        self.assertNotEqual(entry["machine_id"], "192.168.1.100")
        self.assertEqual(entry["machine_id"], generate_machine_id(fp))

        print("Orchestrator successfully updated Registry with Driver & ID.")

if __name__ == '__main__':
    unittest.main()
