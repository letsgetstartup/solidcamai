import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from simco_agent.drivers.opcua.driver import OPCUADriver

@pytest.fixture
def mock_opcua_client():
    with patch("simco_agent.drivers.opcua.driver.Client") as MockClient:
        client_instance = MockClient.return_value
        
        # Async context manager / connect / disconnect
        client_instance.connect = AsyncMock()
        client_instance.disconnect = AsyncMock()
        
        # Mock nodes
        # Map node_id -> return value
        node_values = {
            "ns=2;s=Execution": "ACTIVE",
            "ns=2;s=SpindleSpeed": 1500.0,
            "ns=2;s=PartCount": 99,
            "ns=2;s=Availability": "AVAILABLE"
        }
        
        def get_node_side_effect(node_id):
            m = AsyncMock()
            if node_id in node_values:
                m.read_value.return_value = node_values[node_id]
            else:
                m.read_value.side_effect = Exception("Node not found in mock")
            return m
            
        client_instance.get_node.side_effect = get_node_side_effect
        
        yield client_instance

@pytest.mark.asyncio
async def test_opcua_driver_sample(mock_opcua_client):
    driver = OPCUADriver("opc.tcp://test:4840")
    
    # Connect
    assert await driver.connect() is True
    assert driver.is_connected() is True
    
    # Sample
    points = await driver.sample()
    
    # Verify points
    assert len(points) == 4
    
    exec_pt = next(p for p in points if p.name == "execution_state")
    assert exec_pt.value == "ACTIVE"
    
    spindle_pt = next(p for p in points if p.name == "spindle_speed")
    assert spindle_pt.value == 1500.0
    
    await driver.disconnect()
    assert driver.is_connected() is False
