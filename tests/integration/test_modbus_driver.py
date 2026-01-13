import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from simco_agent.drivers.modbus.driver import ModbusDriver

@pytest.fixture
def mock_modbus_client():
    with patch("simco_agent.drivers.modbus.driver.AsyncModbusTcpClient") as MockClient:
        client_instance = MockClient.return_value
        
        client_instance.connect = AsyncMock(return_value=True)
        client_instance.close = MagicMock()
        
        # Mock registers
        # 100: 1 (ACTIVE)
        # 101: 1 (AVAILABLE)
        # 102: 5000 (RPM)
        
        def read_holding_side_effect(addr, count):
            m = MagicMock()
            m.isError = MagicMock(return_value=False)
            if addr == 100: m.registers = [1]
            elif addr == 101: m.registers = [1]
            elif addr == 102: m.registers = [5000]
            else: m.registers = [0]
            
            # read_holding_registers is a coroutine in pymodbus 3.x async client?
            # Actually, typically it returns response, or it's awaited.
            # In AsyncModbusTcpClient, methods like read_holding_registers are async.
            
            f = asyncio.Future()
            f.set_result(m)
            return f
            
        import asyncio
        client_instance.read_holding_registers.side_effect = read_holding_side_effect
        
        yield client_instance

@pytest.mark.asyncio
async def test_modbus_driver_sample(mock_modbus_client):
    driver = ModbusDriver("modbus-tcp://127.0.0.1:502")
    
    assert await driver.connect() is True
    
    points = await driver.sample()
    assert len(points) == 3
    
    exec_pt = next(p for p in points if p.name == "execution_state")
    assert exec_pt.value == "ACTIVE"
    
    spindle_pt = next(p for p in points if p.name == "spindle_speed")
    assert spindle_pt.value == 5000
    
    await driver.disconnect()
