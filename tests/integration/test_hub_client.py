import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from simco_agent.drivers.hub_client import DriverHubClient
from simco_agent.drivers.selection import DriverSelector
from simco_agent.drivers.common.models import DriverManifest

# Mock aiohttp response
class MockResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status = status

    async def json(self):
        return self._data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_aiohttp():
    with patch("simco_agent.drivers.hub_client.aiohttp.ClientSession") as MockSession:
        session_instance = MockSession.return_value
        
        # Async context manager for session
        session_instance.__aenter__.return_value = session_instance
        session_instance.__aexit__.return_value = None
        
        # Async context manager for get()
        # session.get() -> AsyncContextManager -> Response
        
        mock_get = MagicMock()
        
        # Define success response
        success_data = [
            {
                "name": "fanuc-driver", 
                "version": "1.0", 
                "protocol": "fanuc_focas",
                "match_rules": [{"vendor": "Fanuc"}]
            },
            {
                "name": "haas-driver", 
                "version": "2.0", 
                "protocol": "mtconnect"
            }
        ]
        
        mock_get.return_value = MockResponse(success_data)
        session_instance.get = mock_get
        
        yield session_instance

@pytest.mark.asyncio
async def test_fetch_manifests(mock_aiohttp):
    client = DriverHubClient("http://hub.example.com/manifest.json")
    manifests = await client.fetch_manifests()
    
    assert len(manifests) == 2
    assert manifests[0].name == "fanuc-driver"
    assert manifests[0].protocol == "fanuc_focas"
    assert manifests[1].name == "haas-driver"

@pytest.mark.asyncio
async def test_sync_to_selector(mock_aiohttp):
    client = DriverHubClient("http://hub.example.com/manifest.json")
    selector = DriverSelector()
    
    await client.sync_to_selector(selector)
    
    # Internal list in selector is private _manifests
    assert len(selector._manifests) == 2
    assert selector._manifests[0].name == "fanuc-driver"
