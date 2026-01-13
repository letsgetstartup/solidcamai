import pytest
import pytest_asyncio
from typing import AsyncGenerator
from tests.simulators.mtconnect_server import MTConnectSimulator
from simco_agent.drivers.mtconnect.driver import MTConnectDriver
from simco_agent.drivers.common.base_driver import DriverBase

@pytest_asyncio.fixture
async def mtconnect_simulator() -> AsyncGenerator[MTConnectSimulator, None]:
    # Use non-standard port
    server = MTConnectSimulator(port=17879)
    await server.start()
    yield server
    await server.stop()

@pytest.mark.asyncio
async def test_mtconnect_driver_sample(mtconnect_simulator):
    driver = MTConnectDriver("http://127.0.0.1:17879")
    
    # Check connect
    assert await driver.connect() is True
    assert driver.is_connected() is True
    
    # Check sample
    points = await driver.sample()
    assert len(points) >= 5 # We expect avail, exec, mode, pgm, pc, spindle, load, feed
    
    # Check values
    # Execution
    exec_pt = next(p for p in points if p.name == "execution_state")
    assert exec_pt.value == "ACTIVE"
    
    # Spindle
    spindle_pt = next(p for p in points if p.name == "spindle_speed")
    assert spindle_pt.value == 1200.5
    
    # Feedrate
    feed_pt = next(p for p in points if p.name == "path_feedrate")
    assert feed_pt.value == 500.0
    
    # Part Count
    pc_pt = next(p for p in points if p.name == "part_count")
    assert pc_pt.value == 42
    
    await driver.disconnect()
    assert driver.is_connected() is False
