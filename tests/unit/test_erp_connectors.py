import pytest
from datetime import datetime
from cloud.erp.connectors.base import ErpEntitySpec
from cloud.erp.connectors.registry import get_connector_class, register, _CONNECTORS
from cloud.erp.connectors.sap_b1_service_layer import SapB1ServiceLayerConfig, SapB1ServiceLayerConnector

# --- Registry Tests ---

def test_registry_lookup():
    # Verify SAP B1 is registered by default (since we imported it)
    cls = get_connector_class("sap_b1_service_layer")
    assert cls == SapB1ServiceLayerConnector

def test_registry_invalid():
    with pytest.raises(ValueError):
        get_connector_class("non_existent_provider")

# --- SAP B1 Connector Tests (Mocked) ---

class MockResponse:
    def __init__(self, status_code, json_data, cookies=None):
        self.status_code = status_code
        self._json_data = json_data
        self.cookies = cookies or {}

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

@pytest.mark.asyncio
async def test_sap_b1_healthcheck(monkeypatch):
    # Mock httpx.AsyncClient.post (login) and get (metadata)
    
    async def mock_post(*args, **kwargs):
        return MockResponse(200, {}, cookies={"B1SESSION": "test_session"})
        
    async def mock_get(*args, **kwargs):
        # args[0] is self, args[1] is url
        url = args[1] if len(args) > 1 else kwargs.get("url", "")
        if "Login" in str(url):
             return await mock_post(*args, **kwargs)
        return MockResponse(200, {})

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    cfg = SapB1ServiceLayerConfig(
        base_url="https://mock",
        company_db="test",
        username="u",
        password="p"
    )
    connector = SapB1ServiceLayerConnector(cfg)
    
    res = await connector.healthcheck()
    assert res["ok"] is True
    assert res["status_code"] == 200

@pytest.mark.asyncio
async def test_sap_b1_fetch(monkeypatch):
    # Mock Login
    async def mock_post(*args, **kwargs):
        return MockResponse(200, {}, cookies={"B1SESSION": "test_session"})
    
    # Mock Fetch
    async def mock_get(*args, **kwargs):
        return MockResponse(200, {
            "value": [
                {"ItemCode": "A001", "ItemName": "Test Item"},
                {"ItemCode": "A002", "ItemName": "Test Item 2"}
            ]
        })

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    cfg = SapB1ServiceLayerConfig("https://mock", "db", "u", "p")
    connector = SapB1ServiceLayerConnector(cfg)
    
    items = []
    entity = ErpEntitySpec("items", "Items", "ItemCode")
    
    async for item in connector.fetch(entity, since=None):
        items.append(item)
        
    assert len(items) == 2
    assert items[0]["ItemCode"] == "A001"
