import asyncio
import logging
import time
import random
from typing import Dict, Any, List, Optional
from multiprocessing import Process, Queue
from simco_agent.drivers.factory import DriverFactory
from simco_agent.schemas import MachineInfo, TelemetryPayload
from simco_agent.config import settings

logger = logging.getLogger("simco_agent.driver_manager")

def _worker_func(q, vendor, ip, driver_hub_url, drivers_active_dir):
    """Isolated worker function for driver execution."""
    try:
        from simco_agent.drivers.factory import DriverFactory
        from simco_agent.config import settings
        
        # Pass context into the worker process
        settings.DRIVER_HUB_MANIFEST_URL = driver_hub_url
        settings.DRIVERS_ACTIVE_DIR = drivers_active_dir

        async def run():
            driver = DriverFactory.get_driver(vendor, ip)
            await driver.connect()
            data = await driver.read_telemetry()
            await driver.close()
            q.put({"status": "SUCCESS", "data": data})
        
        asyncio.run(run())
    except Exception as e:
        q.put({"status": "ERROR", "error": str(e)})

class DriverManager:
    """Orchestrates driver execution in isolated workers with timeouts and backoff."""

    def __init__(self):
        self.polling_timeout = 5.0  # Seconds
        self.consecutive_failures: Dict[str, int] = {}
        self.backoff_until: Dict[str, float] = {}
        self.circuit_breaker_threshold = 5

    async def run_poll(self, machines: List[MachineInfo]) -> List[TelemetryPayload]:
        """Runs polling for all machines in parallel with isolation."""
        tasks = [self._poll_machine_isolated(machine) for machine in machines]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def _poll_machine_isolated(self, machine: MachineInfo) -> Optional[TelemetryPayload]:
        machine_id = machine.mac if machine.mac != "Unknown" else machine.ip
        
        # 1. Circuit Breaker / Backoff Check
        now = time.time()
        if machine_id in self.backoff_until and now < self.backoff_until[machine_id]:
            return None

        # 2. Execution with Timeout
        try:
            payload = await asyncio.wait_for(
                self._execute_driver_logic(machine),
                timeout=self.polling_timeout
            )
            
            # Reset failures on success
            self.consecutive_failures[machine_id] = 0
            return payload

        except Exception as e:
            # Catching everything including TimeoutError
            # logger.error(f"Error polling {machine_id}: {e}")
            self._handle_failure(machine_id)
        
        return None

    async def _execute_driver_logic(self, machine: MachineInfo) -> TelemetryPayload:
        """Instantiates and runs driver telemetry collection in a separate process."""
        q = Queue()
        p = Process(target=_worker_func, args=(
            q, 
            machine.vendor, 
            machine.ip, 
            settings.DRIVER_HUB_MANIFEST_URL, 
            settings.DRIVERS_ACTIVE_DIR
        ))
        p.start()
        
        # Wait for worker in a non-blocking way
        try:
            # Polling the queue with a sleep to allow async context switching
            max_wait = 10.0 # Bounded wait
            start_wait = time.time()
            while p.is_alive() and q.empty() and (time.time() - start_wait < max_wait):
                await asyncio.sleep(0.1)
            
            if not q.empty():
                result = q.get()
                if result["status"] == "SUCCESS":
                    raw_data = result["data"]
                    is_anomaly = raw_data.get('spindle_load', 0) > settings.SPINDLE_LOAD_THRESHOLD
                    return TelemetryPayload(
                        machine_id=machine.mac if machine.mac != "Unknown" else machine.ip,
                        status=raw_data.get('status', 'UNKNOWN'),
                        spindle_load=raw_data.get('spindle_load', 0.0),
                        feed_rate=raw_data.get('feed_rate', 0.0),
                        program_name=raw_data.get('program_name'),
                        anomaly=is_anomaly
                    )
                else:
                    raise Exception(result.get("error", "Unknown worker error"))
            else:
                if p.is_alive():
                    p.terminate()
                raise Exception("Worker timed out or crashed without data")
        finally:
            if p.is_alive():
                p.terminate()
                p.join()

    def _handle_failure(self, machine_id: str):
        self.consecutive_failures[machine_id] = self.consecutive_failures.get(machine_id, 0) + 1
        count = self.consecutive_failures[machine_id]
        
        # Exponential Backoff with Jitter
        # Wait = 2^count + random jitter
        wait_time = min(300, (2 ** count)) + random.uniform(0, 1)
        self.backoff_until[machine_id] = time.time() + wait_time
        
        if count >= self.circuit_breaker_threshold:
            logger.critical(f"Circuit Breaker Triggered for {machine_id}! (Failures: {count})")
