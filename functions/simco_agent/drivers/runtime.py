import logging
import asyncio
from typing import Dict, Optional, Type, List
from simco_agent.drivers.common.base_driver import DriverBase
from simco_agent.drivers.common.models import DriverMatch, TelemetryPoint

logger = logging.getLogger(__name__)

class DriverRuntime:
    _impl_registry: Dict[str, Type[DriverBase]] = {}

    def __init__(self):
        self._active_drivers: Dict[str, DriverBase] = {} # machine_id -> driver instance

    @classmethod
    def register_implementation(cls, name: str, impl_class: Type[DriverBase]):
        """
        Register a driver implementation class for a given manifest name.
        """
        cls._impl_registry[name] = impl_class
        logger.info(f"Registered driver implementation '{name}' -> {impl_class.__name__}")

    async def start_driver(self, machine_id: str, match: DriverMatch, endpoint: str) -> bool:
        """
        Instantiate and connect a driver for the machine.
        """
        if machine_id in self._active_drivers:
            logger.warning(f"Driver for {machine_id} already active")
            return True

        driver_name = match.manifest.name
        impl_class = self._impl_registry.get(driver_name)
        
        if not impl_class:
            logger.error(f"No implementation registered for driver '{driver_name}'")
            return False

        try:
            # Instantiate driver. Assumption: constructor takes endpoint as first arg?
            # Or maybe kwargs? Let's assume standard init(endpoint) for now.
            # Real drivers might need more config.
            driver = impl_class(endpoint=endpoint)
            
            logger.info(f"Connecting driver {driver_name} for {machine_id} at {endpoint}...")
            success = await driver.connect()
            
            if success:
                self._active_drivers[machine_id] = driver
                logger.info(f"Driver {driver_name} started for {machine_id}")
                return True
            else:
                logger.error(f"Driver {driver_name} failed to connect to {machine_id}")
                return False

        except Exception as e:
            logger.error(f"Error starting driver {driver_name} for {machine_id}: {e}")
            return False

    async def stop_driver(self, machine_id: str):
        driver = self._active_drivers.get(machine_id)
        if driver:
            try:
                await driver.disconnect()
            except Exception as e:
                logger.warning(f"Error stopping driver for {machine_id}: {e}")
            finally:
                del self._active_drivers[machine_id]
                logger.info(f"Stopped driver for {machine_id}")

    async def sample_all(self) -> Dict[str, List[TelemetryPoint]]:
        """
        Collect telemetry from all active drivers.
        """
        results = {}
        for mid, driver in self._active_drivers.items():
            if driver.is_connected():
                try:
                    points = await driver.sample()
                    results[mid] = points
                except Exception as e:
                    logger.error(f"Sampling failed for {mid}: {e}")
            else:
                # Attempt reconnect strategy here in future
                pass
        return results
