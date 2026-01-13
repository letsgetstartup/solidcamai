import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from simco_agent.discovery.probes.modbus_probe import ModbusProbe
from simco_agent.discovery.fingerprinting import FingerprintOrchestrator

@pytest.fixture
def mock_modbus_client():
    with patch("simco_agent.discovery.probes.modbus_probe.AsyncModbusTcpClient") as MockClient:
        client_instance = MockClient.return_value
        
        # connect is async
        client_instance.connect = AsyncMock(return_value=True)
        # close is sync usually in pymodbus 3?, or async? Code calls client.close() which is sync in some versions.
        # Check code: client.close()
        # Let's mock it safe.
        client_instance.close = MagicMock()
        
        yield client_instance

@pytest.mark.asyncio
async def test_modbus_probe_direct(mock_modbus_client):
    probe = ModbusProbe(timeout=2.0)
    fp = await probe.run("127.0.0.1", 502)
    
    assert fp is not None
    assert fp.protocol == "modbus"
    assert fp.model == "Modbus Device"
    assert fp.confidence >= 0.9
    
    mock_modbus_client.connect.assert_called_once()

@pytest.mark.asyncio
async def test_fingerprint_orchestrator_modbus(mock_modbus_client):
    orch = FingerprintOrchestrator()
    candidates = [{
        "ip": "127.0.0.1",
        "protocol_candidates": [{"port": 502, "protocols": ["modbus"]}]
    }]
    
    results = await orch.run(candidates)
    assert len(results) == 1
    fp = results[0]
    assert fp.protocol == "modbus"
