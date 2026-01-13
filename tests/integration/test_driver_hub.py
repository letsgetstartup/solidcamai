from fastapi.testclient import TestClient
from cloud.control_plane.app import app
from cloud.control_plane.db import Base, get_db, AsyncSessionLocal
from cloud.control_plane.driver_hub import driver_hub
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest
import pytest_asyncio
import asyncio

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
    
    # Manually seed for test env (startup event might not trigger exactly right or share the same memory db if we are not careful)
    # Actually, app startup event runs in context of main app.
    # We should trigger seeding manually on test_db to be sure.
    async with TestingSessionLocal() as session:
         await driver_hub.seed_defaults(session)

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client(test_db):
    return TestClient(app)

def test_list_drivers(client):
    res = client.get("/drivers")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    
    ids = [d["driver_id"] for d in data]
    assert "mtconnect" in ids
    assert "opcua" in ids
    assert "modbus" in ids

def test_download_driver(client):
    res = client.get("/drivers/mtconnect/1.0.0/download")
    assert res.status_code == 200
    assert "url" in res.json()
    assert "googleapis" in res.json()["url"]
