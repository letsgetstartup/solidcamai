from fastapi.testclient import TestClient
from cloud.control_plane.app import app
from cloud.control_plane.db import engine, Base, get_db, GatewayStatus
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest
import pytest_asyncio
import datetime

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
def client(test_db):
    return TestClient(app)

def test_heartbeat_updates_last_seen(client):
    headers = {"Authorization": "Bearer u_admin:admin@simco.ai"}
    # 1. Setup Tenant, Site, Gateway
    client.post("/tenants", json={"tenant_id": "t1", "name": "T1"}, headers=headers)
    client.post("/sites", json={"site_id": "s1", "tenant_id": "t1", "name": "S1"}, headers=headers)
    
    # Gateway creation also likely needs headers if I secured it, but check app.py. 
    # Even if not, it depends on site.
    client.post("/gateways", json={"gateway_id": "gw1", "tenant_id": "t1", "site_id": "s1", "display_name": "G1"})
    
    # Verify initial state
    res = client.get("/gateways/gw1")
    assert res.json()["status"] == "PROVISIONING"
    # last_seen should be null or old
    
    # 2. Send Heartbeat
    hb_payload = {
        "uptime_seconds": 100,
        "local_ip": "192.168.1.50",
        "agent_version": "3.1.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    res = client.post("/gateways/gw1/heartbeat", json=hb_payload)
    assert res.status_code == 200
    
    # 3. Verify Update
    res = client.get("/gateways/gw1")
    data = res.json()
    assert data["last_seen"] is not None
    # Note: Status update logic in app.py only changes OFFLINE -> ACTIVE, 
    # PROVISIONING might stick until explicit activation? 
    # Let's check logic: if db_gw.status == GatewayStatus.OFFLINE: set ACTIVE
    # If it stays PROVISIONING, that's fine for now.
