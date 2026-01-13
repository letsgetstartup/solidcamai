from fastapi.testclient import TestClient
from cloud.control_plane.app import app
from cloud.control_plane.db import engine, Base, get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest
import pytest_asyncio
import os

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture
async def test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client(test_db): # Depend on DB init
    return TestClient(app)

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "control-plane"}

def test_create_read_tenant(client):
    response = client.post("/tenants", json={"tenant_id": "t1", "name": "Tenant 1"})
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "t1"
    
    response = client.get("/tenants/t1")
    assert response.status_code == 200
    assert response.json()["name"] == "Tenant 1"

def test_site_flow(client):
    # Setup Tenant
    client.post("/tenants", json={"tenant_id": "t1", "name": "T1"})
    
    # Create Site
    response = client.post("/sites", json={"site_id": "s1", "tenant_id": "t1", "name": "Site 1"})
    assert response.status_code == 200
    
    # Verify Site
    response = client.get("/sites/s1")
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "t1"

def test_gateway_flow(client):
    # Setup
    client.post("/tenants", json={"tenant_id": "t1", "name": "T1"})
    client.post("/sites", json={"site_id": "s1", "tenant_id": "t1", "name": "S1"})
    
    # Create Gateway
    response = client.post("/gateways", json={
        "gateway_id": "gw1",
        "tenant_id": "t1",
        "site_id": "s1",
        "display_name": "GW 1"
    })
    assert response.status_code == 200
    
    # Verify Status
    data = response.json()
    assert data["status"] == "PROVISIONING"
