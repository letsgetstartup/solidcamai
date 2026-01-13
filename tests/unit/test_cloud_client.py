import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from simco_agent.cloud.client import CloudClient
from simco_agent.cloud.auth import AuthProvider
from simco_agent.drivers.common.models import TelemetryPoint

# Mock response class
class MockResponse:
    def __init__(self, status=200):
        self.status = status
    
    async def text(self):
        return "OK"

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_aiohttp():
    with patch("simco_agent.cloud.client.aiohttp.ClientSession") as MockSession:
        session_instance = MockSession.return_value
        session_instance.__aenter__.return_value = session_instance
        session_instance.__aexit__.return_value = None
        
        post_mock = MagicMock()
        post_mock.return_value = MockResponse(200)
        session_instance.post = post_mock
        
        yield session_instance

@pytest.mark.asyncio
async def test_send_telemetry(mock_aiohttp):
    auth = AuthProvider("test-key")
    client = CloudClient("https://api.simco.io", auth)
    
    points = [TelemetryPoint("p1", 123, "t1")]
    
    result = await client.send_telemetry(points)
    assert result is True
    
    # Verify auth header
    # Access the mock session instance used inside context manager
    session_instance = mock_aiohttp
    session_instance.post.assert_called_once()
    
    args, kwargs = session_instance.post.call_args
    assert args[0] == "https://api.simco.io/api/v1/ingest"
    assert "Authorization" in kwargs["headers"]
    assert "application/json" in kwargs["headers"]["Content-Type"]
    assert len(kwargs["json"]) == 1
    assert kwargs["json"][0]["name"] == "p1"
