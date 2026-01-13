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

def test_rbac_flow(client):
    owner_token = "u_owner:owner@simco.ai"
    other_token = "u_other:other@simco.ai"
    
    # 1. Create Tenant as Owner (should auto-assign role)
    res = client.post(
        "/tenants", 
        json={"tenant_id": "t1", "name": "Secured Tenant"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert res.status_code == 200
    
    # 2. Owner can read
    res = client.get(
        "/tenants/t1", 
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert res.status_code == 200
    
    # 3. Random User cannot read
    res = client.get(
        "/tenants/t1", 
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert res.status_code == 403
    
    # 4. Random User cannot create site in that tenant
    res = client.post(
        "/sites", 
        json={"site_id": "s1", "tenant_id": "t1", "name": "Site 1"},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert res.status_code == 403
    
    # 5. Owner can create site
    res = client.post(
        "/sites", 
        json={"site_id": "s1", "tenant_id": "t1", "name": "Site 1"},
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert res.status_code == 200
