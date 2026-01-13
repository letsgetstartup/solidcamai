from fastapi.testclient import TestClient
from cloud.control_plane.app import app
from cloud.control_plane.db import Base, get_db
from simco_agent.core.identity import IdentityManager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import pytest
import pytest_asyncio
import os
import shutil

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_PKI_DIR = "./test_pki"

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

@pytest.fixture
def identity_manager():
    if os.path.exists(TEST_PKI_DIR):
        shutil.rmtree(TEST_PKI_DIR)
    os.makedirs(TEST_PKI_DIR)
    return IdentityManager(pki_dir=TEST_PKI_DIR)

def test_csr_signing_flow(client, identity_manager):
    # 1. Setup Tenant/Site
    client.post("/tenants", json={"tenant_id": "cust1", "name": "Customer 1"})
    client.post("/sites", json={"site_id": "site1", "tenant_id": "cust1", "name": "Workshop 1"})

    # 2. Init Enrollment
    init_data = client.post("/enroll/init").json()
    code = init_data["claim_code"]
    token = init_data["poll_token"]
    
    # 3. Simulate User Claiming Code
    client.post("/gateways/claim", json={"claim_code": code, "site_id": "site1", "tenant_id": "cust1"})
    
    # 4. Agent Generates CSR
    # Note: Gateway ID is not known yet by agent in real flow until poll success, 
    # but let's assume agent gets it from poll
    poll_res = client.post("/enroll/poll", params={"poll_token": token}).json()
    gateway_id = poll_res["gateway_id"]
    
    csr_pem = identity_manager.generate_csr(gateway_id)
    assert "BEGIN CERTIFICATE REQUEST" in csr_pem
    
    # 5. Agent Requests Signing (using Poll Token for Auth)
    sign_res = client.post("/pki/sign", json={
        "csr_pem": csr_pem,
        "poll_token": token 
    })
    
    assert sign_res.status_code == 200
    cert_data = sign_res.json()
    cert_pem = cert_data["certificate_pem"]
    
    assert "BEGIN CERTIFICATE" in cert_pem
    
    # 6. Agent Stores Cert
    identity_manager.store_cert(cert_pem)
    assert os.path.exists(os.path.join(TEST_PKI_DIR, "device.crt"))

    # Cleanup
    shutil.rmtree(TEST_PKI_DIR)
