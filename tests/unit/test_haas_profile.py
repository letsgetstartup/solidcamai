import unittest
import json
from simco_agent.drivers.common.models import Fingerprint, DriverManifest
from simco_agent.drivers.selection import DriverSelector

class TestHaasProfile(unittest.TestCase):
    def test_haas_profile_matching(self):
        # Load manifest
        with open("simco_agent/manifests/haas_dt2.json", "r") as f:
            data = json.load(f)
            manifest = DriverManifest(
                name=data["name"],
                version=data["version"],
                protocol=data["protocol"],
                match_rules=data["match_rules"]
            )
            
        selector = DriverSelector()
        selector.register_driver(manifest)
        
        # Test 1: Exact Match (DT-2)
        fp = Fingerprint(
            ip="1.2.3.4",
            protocol="mtconnect",
            vendor="Haas Automation",
            model="DT-2"
        )
        match = selector.select_best_match(fp)
        self.assertIsNotNone(match)
        self.assertEqual(match.manifest.name, "haas-mtconnect")
        self.assertIn("Rule match: Vendor, Model", match.reasons[1] if len(match.reasons)>1 else str(match.reasons))
        
        # Test 2: Partial Match (VF-2)
        fp2 = Fingerprint(
            ip="1.2.3.5",
            protocol="mtconnect",
            vendor="Haas Automation",
            model="VF-2"
        )
        match2 = selector.select_best_match(fp2)
        self.assertIsNotNone(match2)
        
        # Test 3: No Match (different vendor)
        fp3 = Fingerprint(
            ip="1.2.3.6",
            protocol="mtconnect",
            vendor="Mazak"
        )
        match3 = selector.select_best_match(fp3)
        self.assertIsNone(match3) # Strict rules prevent this specific driver from matching generic
