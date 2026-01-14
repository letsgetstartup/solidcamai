import unittest
import hashlib
import os
import sys
import shutil

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.drivers.loader import SecureDriverLoader, SecurityError
from simco_agent.drivers.common.models import DriverManifest

TEST_DRIVER_DIR = "/tmp/simco_drivers_test"
TEST_DRIVER_NAME = "test_driver"
TEST_DRIVER_FILE = os.path.join(TEST_DRIVER_DIR, "test_driver.py")

class TestSecureLoader(unittest.TestCase):
    
    def setUp(self):
        if os.path.exists(TEST_DRIVER_DIR):
            shutil.rmtree(TEST_DRIVER_DIR)
        os.makedirs(TEST_DRIVER_DIR)
        
        # Create a valid driver file
        with open(TEST_DRIVER_FILE, "w") as f:
            f.write("def run():\n    return 'safe_code'")
            
    def _compute_hash(self, path):
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def test_integrity_check(self):
        loader = SecureDriverLoader(drivers_root=TEST_DRIVER_DIR)
        valid_hash = self._compute_hash(TEST_DRIVER_FILE)
        
        # Case 1: Valid Load
        manifest = DriverManifest(
            name="test-driver",
            version="1.0",
            checksum=valid_hash
        )
        
        module = loader.load_driver(manifest)
        self.assertIsNotNone(module)
        self.assertEqual(module.run(), "safe_code")
        print("Secure Load: SUCCESS")
        
        # Case 2: Tampering
        with open(TEST_DRIVER_FILE, "a") as f:
            f.write("\nprint('malicious injection')")
            
        print("Tampering with driver file...")
        
        # Manifest still expects old hash
        with self.assertRaises(SecurityError):
            loader.load_driver(manifest)
            
        print("Tamper Detection: SUCCESS")

if __name__ == '__main__':
    unittest.main()
