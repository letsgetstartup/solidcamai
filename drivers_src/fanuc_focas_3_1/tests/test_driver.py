import unittest
from drivers_src.fanuc_focas_3_1.driver import FanucDriver

class TestFanucDriver(unittest.TestCase):
    def test_connection(self):
        driver = FanucDriver("127.0.0.1")
        self.assertTrue(driver.connect())
        self.assertTrue(driver.connected)
        driver.close()
        self.assertFalse(driver.connected)

    def test_data_fetch(self):
        driver = FanucDriver("127.0.0.1")
        driver.connect()
        data = driver.get_data()
        self.assertIn("spindle_load", data)
        self.assertEqual(data["status"], "RUNNING")
        driver.close()

if __name__ == "__main__":
    unittest.main()
