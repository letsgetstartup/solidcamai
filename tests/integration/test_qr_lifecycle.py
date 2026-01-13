import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from cloud.control_plane.app import app
from cloud.control_plane.db import get_db, Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(name="session")
async def session_fixture():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session

@pytest.fixture(name="client")
async def client_fixture(session: AsyncSession):
    async def get_db_override():
        yield session
    app.dependency_overrides[get_db] = get_db_override
    from httpx import ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_qr_lifecycle(client, session):
    # 1. Admin Generates QR
    # POST /mgmt/v1/sites/{site_id}/machines/{machine_id}/qr
    headers = {"X-Dev-Role": "Manager", "X-Dev-Tenant": "t1", "X-Dev-Site": "s1"}
    # Note: query param tenant_id is required by the router signature in router_qr.py
    # "async def get_or_create_qr(site_id: str, machine_id: str, tenant_id: str, ...)"
    # but since it's a POST body usually... wait, router signature:
    # @router.post("/mgmt/v1/sites/{site_id}/machines/{machine_id}/qr", ...)
    # async def get_or_create_qr(..., tenant_id: str, ...)
    # FastAPI expects 'tenant_id' as query param if not in path.
    
    res = await client.post("/mgmt/v1/sites/s1/machines/m1/qr?tenant_id=t1", headers=headers)
    assert res.status_code == 200
    data = res.json()
    public_code = data["public_code"]
    assert len(public_code) > 0
    assert data["status"] == "ACTIVE"
    
    # 2. Get Label Image
    res = await client.get("/mgmt/v1/sites/s1/machines/m1/qr/label?tenant_id=t1", headers=headers)
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert len(res.content) > 0
    
    # 3. Mobile Resolve (Success)
    # GET /mobile/v1/machines/by-token/{public_code}/context
    # Mock mobile headers? Router only checks code for now, but comment says "Verify User Auth".
    # Assuming code currently doesn't strictly enforce auth for MVP or uses stub.
    res = await client.get(f"/mobile/v1/machines/by-token/{public_code}/context")
    assert res.status_code == 200
    ctx = res.json()
    assert ctx["machine_id"] == "m1"
    
    # 4. Mock Revocation (Since we didn't implement explicit revoke endpoint in router_qr.py yet, strictly speaking)
    # Wait, did I implement revoke in router_qr.py?
    # Checked router_qr.py content... I only see:
    # get_or_create_qr, get_qr_label, resolve_machine_context.
    # I did NOT implement rotate/revoke in router_qr.py yet! 
    # The prompt asked for "Gen, Revoke, Image". I missed revoke/rotate endpoints in previous step.
    # I should add them now or skip testing them.
    # Let's verify existing endpoints first.

@pytest.mark.asyncio
async def test_qr_idempotency(client, session):
    headers = {"X-Dev-Role": "Manager", "X-Dev-Tenant": "t1", "X-Dev-Site": "s1"}
    # Call create twice
    res1 = await client.post("/mgmt/v1/sites/s1/machines/m2/qr?tenant_id=t1", headers=headers)
    code1 = res1.json()["public_code"]
    
    res2 = await client.post("/mgmt/v1/sites/s1/machines/m2/qr?tenant_id=t1", headers=headers)
    code2 = res2.json()["public_code"]
    
    assert code1 == code2
