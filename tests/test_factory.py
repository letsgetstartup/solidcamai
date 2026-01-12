import unittest
from simco_agent.drivers.factory import DriverFactory
from simco_agent.drivers.fanuc import FanucDriver

class TestDriverFactory(unittest.TestCase):
    def test_get_fanuc_driver(self):
        driver = DriverFactory.get_driver("Fanuc", "192.168.1.10")
        self.assertIsInstance(driver, FanucDriver)
        self.assertEqual(driver.ip, "192.168.1.10")

    def test_get_unknown_driver(self):
        from simco_agent.drivers.generic import GenericProtocolDriver
        driver = DriverFactory.get_driver("UnknownVendor", "192.168.1.10")
        self.assertIsInstance(driver, GenericProtocolDriver)

if __name__ == '__main__':
    unittest.main()
