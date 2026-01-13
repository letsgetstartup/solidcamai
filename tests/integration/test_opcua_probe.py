import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from simco_agent.discovery.probes.opcua_probe import OPCUAProbe
from simco_agent.discovery.fingerprinting import FingerprintOrchestrator
from asyncua import ua

# Mock Client instead of real server due to Python 3.14/asyncua issues
@pytest.fixture
def mock_opcua_client():
    with patch("simco_agent.discovery.probes.opcua_probe.Client") as MockClient:
        client_instance = MockClient.return_value
        
        # Async context manager mock
        client_instance.__aenter__.return_value = client_instance
        client_instance.__aexit__.return_value = None
        
        # Mock node reading
        # node = client.get_node(id)
        # node.read_value() -> coroutine
        
        mock_node = AsyncMock()
        mock_node.read_value.side_effect = ["Siemens", "Sinumerik 840D sl", "4.7 SP2"]
        
        client_instance.get_node.return_value = mock_node
        
        yield client_instance

@pytest.mark.asyncio
async def test_opcua_probe_direct(mock_opcua_client):
    probe = OPCUAProbe(timeout=2.0)
    fp = await probe.run("127.0.0.1", 4842)
    
    assert fp is not None
    assert fp.protocol == "opcua"
    assert fp.vendor == "Siemens"
    assert fp.model == "Sinumerik 840D sl"
    assert fp.confidence >= 0.9

@pytest.mark.asyncio
async def test_fingerprint_orchestrator_opcua(mock_opcua_client):
    orch = FingerprintOrchestrator()
    candidates = [{
        "ip": "127.0.0.1",
        "protocol_candidates": [{"port": 4842, "protocols": ["opcua"]}]
    }]
    
    results = await orch.run(candidates)
    assert len(results) == 1
    fp = results[0]
    assert fp.protocol == "opcua"
    assert fp.vendor == "Siemens"
