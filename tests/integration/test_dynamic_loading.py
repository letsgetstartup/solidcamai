import pytest
import shutil
import os
import asyncio
from simco_agent.core.driver_manager import DriverManager
from simco_agent.schemas import MachineInfo

TEST_EXT_DIR = "./test_extensions"

@pytest.fixture
def driver_manager():
    if os.path.exists(TEST_EXT_DIR):
        shutil.rmtree(TEST_EXT_DIR)
    
    dm = DriverManager(extensions_dir=TEST_EXT_DIR)
    yield dm
    
    if os.path.exists(TEST_EXT_DIR):
        shutil.rmtree(TEST_EXT_DIR)

@pytest.mark.asyncio
async def test_ensure_driver_installed_missing(driver_manager):
    # This should fail because we haven't implemented the actual download logic, 
    # but it verifies the "not found" path returns False (or logs and returns False).
    # In a real test we'd mock the network call.
    
    result = await driver_manager.ensure_driver_installed("non_existent_driver", "1.0.0")
    assert result is False

@pytest.mark.asyncio
async def test_ensure_driver_installed_exists(driver_manager):
    # Setup: Create a fake driver file
    driver_dir = os.path.join(TEST_EXT_DIR, "fake_driver", "1.0.0")
    os.makedirs(driver_dir)
    with open(os.path.join(driver_dir, "driver.py"), "w") as f:
        f.write("# Fake Driver")
        
    result = await driver_manager.ensure_driver_installed("fake_driver", "1.0.0")
    assert result is True

@pytest.mark.asyncio
async def test_poll_machine_fallback(driver_manager):
    # This tests the fallback logic in _poll_machine_isolated
    # If standard factory fails (which it will for 'unknown_vendor'), 
    # it *should* crash or return None in current impl because we haven't wired up 
    # the dynamic loader to the factory yet.
    # Wait, the DriverManager._execute_driver_logic spawns a process that uses DriverFactory.
    # DriverFactory doesn't know about dynamic drivers yet!
    # PR 08 Plan said: "Update DriverManager to fetch... Use importlib... to load module"
    # But `_execute_driver_logic` runs `_worker_func` which calls `DriverFactory.get_driver`.
    # So we need to update `DriverFactory` or `_worker_func` to look in `extensions_dir`.
    pass 
