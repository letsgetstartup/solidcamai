import unittest
import asyncio
import time
from simco_agent.core.driver_manager import DriverManager
from simco_agent.schemas import MachineInfo

class TestDriverIsolation(unittest.TestCase):
    def setUp(self):
        self.manager = DriverManager()
        self.manager.polling_timeout = 1.0 # Short timeout for tests

    def test_timeout_isolation(self):
        print("\n--- Testing Timeout Isolation ---")
        # Use an IP that triggers hang in GenericProtocolDriver
        machine = MachineInfo(ip="TEST_HANG", mac="MOCK_HANG", vendor="Generic", status="active")
        
        start = time.time()
        async def run():
            return await self.manager.run_poll([machine])
        
        results = asyncio.run(run())
        elapsed = time.time() - start
        
        print(f"Elapsed: {elapsed:.2f}s")
        # Expecting elapsed to be around the polling_timeout (1s), not the driver's sleep (10s)
        self.assertLess(elapsed, 4.0, "Ingest cycle took too long; isolation failed")
        self.assertEqual(len(results), 0, "Should have received no results from hanging driver")
        print("OK: Timeout isolated.")

    def test_circuit_breaker(self):
        print("\n--- Testing Circuit Breaker ---")
        # Use an IP that triggers failure in GenericProtocolDriver
        machine = MachineInfo(ip="TEST_FAIL", mac="MOCK_FAIL", vendor="Generic", status="active")
        
        async def run():
            # Trigger 5 failures
            for _ in range(5):
                # Bypass backoff for rapid testing
                self.manager.backoff_until.clear()
                await self.manager.run_poll([machine])
        
        asyncio.run(run())
        failures = self.manager.consecutive_failures.get("MOCK_FAIL", 0)
        print(f"Consecutive Failures: {failures}")
        self.assertGreaterEqual(failures, 5, "Circuit breaker didn't count failures correctly")
        print("OK: Circuit breaker triggered.")

if __name__ == "__main__":
    unittest.main()
