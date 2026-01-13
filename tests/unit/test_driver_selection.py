import unittest
from simco_agent.drivers.common.models import Fingerprint, DriverManifest
from simco_agent.drivers.selection import DriverSelector

class TestDriverSelection(unittest.TestCase):
    def setUp(self):
        self.selector = DriverSelector()
        
        # 1. Generic Fanuc Driver
        self.selector.register_driver(DriverManifest(
            name="fanuc-generic",
            version="1.0.0",
            protocol="fanuc_focas"
        ))
        
        # 2. Specific Haas MTConnect Driver
        self.selector.register_driver(DriverManifest(
            name="haas-mtconnect",
            version="2.1.0",
            protocol="mtconnect",
            match_rules=[{"vendor": "Haas.*", "model": "VF.*"}]
        ))
        
        # 3. Generic MTConnect Driver
        self.selector.register_driver(DriverManifest(
            name="mtconnect-generic",
            version="1.0.0",
            protocol="mtconnect"
        ))

    def test_exact_match(self):
        fp = Fingerprint(
            ip="1.2.3.4",
            protocol="mtconnect",
            vendor="Haas Automation",
            model="VF-2"
        )
        match = self.selector.select_best_match(fp)
        
        self.assertIsNotNone(match)
        self.assertEqual(match.manifest.name, "haas-mtconnect")
        self.assertGreater(match.score, 0.9) # Protocol (0.4) + Vendor (0.3) + Model (0.3) = 1.0

    def test_generic_fallback(self):
        fp = Fingerprint(
            ip="1.2.3.4",
            protocol="mtconnect",
            vendor="Mazak",
            model="Variaxis"
        )
        match = self.selector.select_best_match(fp)
        
        self.assertIsNotNone(match)
        self.assertEqual(match.manifest.name, "mtconnect-generic")
        self.assertEqual(match.score, 0.4) # Only protocol match

    def test_protocol_mismatch(self):
        fp = Fingerprint(
            ip="1.2.3.4",
            protocol="unknown_proto"
        )
        match = self.selector.select_best_match(fp)
        self.assertIsNone(match)
