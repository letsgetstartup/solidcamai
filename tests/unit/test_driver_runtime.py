import pytest
import pytest_asyncio
from typing import List
from simco_agent.drivers.common.base_driver import DriverBase
from simco_agent.drivers.common.models import TelemetryPoint, DriverMatch, DriverManifest
from simco_agent.drivers.runtime import DriverRuntime

class MockDriver(DriverBase):
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.connected = False

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def disconnect(self):
        self.connected = False

    async def sample(self) -> List[TelemetryPoint]:
        return [TelemetryPoint(name="mock_signal", value=123, timestamp="2023-01-01")]

    def is_connected(self) -> bool:
        return self.connected

@pytest.fixture
def runtime():
    r = DriverRuntime()
    # Register mock driver
    DriverRuntime.register_implementation("mock-driver", MockDriver)
    return r

@pytest.mark.asyncio
async def test_driver_lifecycle(runtime):
    manifest = DriverManifest(name="mock-driver", version="1.0")
    match = DriverMatch(manifest=manifest, score=1.0)
    
    # 1. Start
    success = await runtime.start_driver("machine-1", match, "mock://test")
    assert success is True
    assert "machine-1" in runtime._active_drivers
    driver = runtime._active_drivers["machine-1"]
    assert driver.is_connected()
    assert driver.endpoint == "mock://test"

    # 2. Sample
    results = await runtime.sample_all()
    assert "machine-1" in results
    points = results["machine-1"]
    assert len(points) == 1
    assert points[0].value == 123

    # 3. Stop
    await runtime.stop_driver("machine-1")
    assert "machine-1" not in runtime._active_drivers
    assert not driver.is_connected()
