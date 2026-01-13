from fastapi.testclient import TestClient
from cloud.control_plane.app import app
from cloud.control_plane.db import engine, Base, get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest
import pytest_asyncio

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

def test_full_enrollment_flow(client):
    # 1. Setup Tenant & Site
    client.post("/tenants", json={"tenant_id": "cust1", "name": "Customer 1"})
    client.post("/sites", json={"site_id": "site1", "tenant_id": "cust1", "name": "Workshop 1"})

    # 2. Gateway Inits
    init_res = client.post("/enroll/init")
    assert init_res.status_code == 200
    data = init_res.json()
    claim_code = data["claim_code"]
    poll_token = data["poll_token"]
    assert len(claim_code) == 6
    
    # 3. Gateway Polls (Should be WAITING)
    poll_res = client.post("/enroll/poll", params={"poll_token": poll_token})
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "WAITING"

    # 4. User Claims Code
    claim_res = client.post("/gateways/claim", json={
        "claim_code": claim_code,
        "site_id": "site1",
        "tenant_id": "cust1"
    })
    assert claim_res.status_code == 200
    assert claim_res.json()["status"] == "claimed"

    # 5. Gateway Polls (Should be SUCCESS)
    poll_res = client.post("/enroll/poll", params={"poll_token": poll_token})
    assert poll_res.status_code == 200
    final_data = poll_res.json()
    assert final_data["status"] == "SUCCESS"
    assert "gateway_id" in final_data
    assert final_data["config"]["site_id"] == "site1"
    
    # Verify Gateway Record Exists
    gw_id = final_data["gateway_id"]
    gw_res = client.get(f"/gateways/{gw_id}")
    assert gw_res.status_code == 200
    assert gw_res.json()["tenant_id"] == "cust1"
