from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from .db import init_db, get_db, GatewayStatus, AsyncSessionLocal
import datetime
from . import crud

app = FastAPI(title="SIMCO Control Plane", version="3.1.0")

# --- Pydantic Schemas for API ---
class TenantCreate(BaseModel):
    tenant_id: str
    name: str

class SiteCreate(BaseModel):
    site_id: str
    tenant_id: str
    name: str

class GatewayCreate(BaseModel):
    gateway_id: str
    tenant_id: str
    site_id: str
    display_name: str

class TenantResponse(BaseModel):
    tenant_id: str
    name: str
    class Config:
        from_attributes = True

class SiteResponse(BaseModel):
    site_id: str
    tenant_id: str
    name: str
    class Config:
        from_attributes = True
        
class GatewayResponse(BaseModel):
    gateway_id: str
    tenant_id: str
    site_id: str
    display_name: str
    status: str
    last_seen: Optional[datetime.datetime] = None
    class Config:
        from_attributes = True

@app.on_event("startup")
async def startup():
    # Ensure ERP models are imported before create_all
    from . import models_erp  # noqa: F401
    from . import models_qr   # noqa: F401
    await init_db()
    
    # OpenTelemetry Setup
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        
        # In PROD, use OTLPSpanExporter
        provider = TracerProvider()
        # For MVP/Dev, just log to console or no-op if no exporter configured
        # provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        trace.set_tracer_provider(provider)
        
        FastAPIInstrumentor.instrument_app(app)
        print("OpenTelemetry instrumentation enabled.")
    except ImportError:
        print("OpenTelemetry not installed, skipping.")

# --- Auth ---
from .auth import get_user_with_roles, CurrentUser, check_access

# --- Endpoints ---
@app.get("/health")
async def health():
    return {"status": "ok", "service": "control-plane"}

@app.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant: TenantCreate, 
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_user_with_roles)
):
    # Only System Admin or similar can create tenants? 
    # For now, let any auth user create one, but they become OWNER.
    db_tenant = await crud.get_tenant(db, tenant.tenant_id)
    if db_tenant:
        raise HTTPException(status_code=400, detail="Tenant already exists")
        
    new_t = await crud.create_tenant(db, tenant.tenant_id, tenant.name)
    
    # Auto-assign OWNER
    from .db import Membership, UserRole
    # Ensure user exists (stub sync)
    from sqlalchemy.future import select
    from .db import User
    
    # Check if user exists, else create
    u = await db.execute(select(User).where(User.user_id == user.user_id))
    if not u.scalars().first():
         db.add(User(user_id=user.user_id, email=user.email))
    
    db.add(Membership(tenant_id=new_t.tenant_id, user_id=user.user_id, role=UserRole.OWNER))
    await db.commit()
    
    return new_t

@app.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def read_tenant(
    tenant_id: str, 
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_user_with_roles)
):
    if not check_access(user, tenant_id):
         raise HTTPException(status_code=403, detail="Access denied to this tenant")

    db_tenant = await crud.get_tenant(db, tenant_id)
    if db_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return db_tenant

@app.post("/sites", response_model=SiteResponse)
async def create_site(
    site: SiteCreate, 
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_user_with_roles)
):
    if not check_access(user, site.tenant_id):
         raise HTTPException(status_code=403, detail="Access denied to this tenant")
         
    # Validate tenant exists
    if not await crud.get_tenant(db, site.tenant_id):
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    db_site = await crud.get_site(db, site.site_id)
    if db_site:
         raise HTTPException(status_code=400, detail="Site already exists")
    return await crud.create_site(db, site.site_id, site.tenant_id, site.name)

@app.get("/sites/{site_id}", response_model=SiteResponse)
async def read_site(site_id: str, db: AsyncSession = Depends(get_db)):
    db_site = await crud.get_site(db, site_id)
    if db_site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return db_site

from .router_erp import router as erp_router
app.include_router(erp_router)
from .router_qr import router as qr_router
app.include_router(qr_router)
from .router_display import router as display_router
app.include_router(display_router)

@app.post("/gateways", response_model=GatewayResponse)
async def create_gateway(gateway: GatewayCreate, db: AsyncSession = Depends(get_db)):
    # Validate site
    if not await crud.get_site(db, gateway.site_id):
         raise HTTPException(status_code=404, detail="Site not found")

    db_gw = await crud.get_gateway(db, gateway.gateway_id)
    if db_gw:
         raise HTTPException(status_code=400, detail="Gateway already exists")
    return await crud.create_gateway(db, gateway.gateway_id, gateway.tenant_id, gateway.site_id, gateway.display_name)

@app.get("/gateways/{gateway_id}", response_model=GatewayResponse)
async def read_gateway(gateway_id: str, db: AsyncSession = Depends(get_db)):
    db_gw = await crud.get_gateway(db, gateway_id)
    if db_gw is None:
        raise HTTPException(status_code=404, detail="Gateway not found")
    return db_gw

# --- Enrollment Endpoints ---
from .enrollment import enrollment_manager, register_claimed_gateway

class EnrollInitResponse(BaseModel):
    claim_code: str
    poll_token: str
    expires_in_seconds: int = 900

class ClaimRequest(BaseModel):
    claim_code: str
    site_id: str
    tenant_id: str

class EnrollPollResponse(BaseModel):
    status: str
    gateway_id: Optional[str] = None
    config: Optional[dict] = None

@app.post("/enroll/init", response_model=EnrollInitResponse)
async def enroll_init():
    code, token = enrollment_manager.generate_code()
    return {"claim_code": code, "poll_token": token}

@app.post("/gateways/claim")
async def claim_gateway(req: ClaimRequest):
    success = enrollment_manager.claim_code(req.claim_code, req.site_id, req.tenant_id)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    return {"status": "claimed"}

@app.post("/enroll/poll", response_model=EnrollPollResponse)
async def enroll_poll(poll_token: str, db: AsyncSession = Depends(get_db)):
    status = enrollment_manager.get_status(poll_token)
    if not status:
        raise HTTPException(status_code=401, detail="Invalid poll token")
        
    if status["status"] == "WAITING":
        return {"status": "WAITING"}
        
    if status["status"] == "CLAIMED":
        # Finalize and return grant
        gw = await register_claimed_gateway(db, enrollment_manager._temp_ids[poll_token])
        if not gw:
             return {"status": "ERROR"}
             
        # In real life, return a stronger token or signed config
        return {
            "status": "SUCCESS", 
            "gateway_id": gw.gateway_id,
            "config": {
                "tenant_id": gw.tenant_id, 
                "site_id": gw.site_id,
                "control_plane_url": "http://localhost:8080"
            }
        }

# --- PKI Endpoints ---
from .ca import ca_service

class SignRequest(BaseModel):
    csr_pem: str
    poll_token: Optional[str] = None # Used during initial enrollment
    # gateway_id: Optional[str] = None # Used during rotation (authenticated via mTLS)

@app.post("/pki/sign")
async def sign_csr(req: SignRequest, db: AsyncSession = Depends(get_db)):
    gateway_id = None
    
    # 1. Enroll Flow: Validate via Poll Token
    if req.poll_token:
        status = enrollment_manager.get_status(req.poll_token)
        if not status or status["status"] != "CLAIMED":
             raise HTTPException(status_code=401, detail="Invalid or unclaimed poll token")
        # Get the temp_id -> final_id
        gw_temp_id = enrollment_manager._temp_ids[req.poll_token] 
        # Wait, enrollment_manager needs to track the final ID better
        # We need to look up the final gateway ID we just created in enroll_poll
        # Ideally, enrolling client calls /poll to get ID, then calls /sign with token + ID
        # For simplicity, let's assume the token grants rights to sign for the gateway it's bound to.
        # We need to find the gateway record created for this token.
        
        # Let's simple look up by querying AuditLogs or modifying enrollment manager to store final_id
        entry = enrollment_manager._codes.get(enrollment_manager._temp_ids[req.poll_token])

        # If we can't find it easily this way, let's hack it:
        # Client MUST provide the gateway_id returned in /poll response?
        # Let's trust the token binds to one identity.
        if entry.get("final_gateway_id"):
             gateway_id = entry["final_gateway_id"]
        else:
             raise HTTPException(status_code=400, detail="Enrollment not complete")

    # 2. Rotation Flow: Validate via Valid mTLS (TODO: integration)
    # else: 
    #    gateway_id = request.state.gateway_id
    
    if not gateway_id:
        raise HTTPException(status_code=401, detail="Not authorized")
        
    # Sign
    cert_pem = ca_service.sign_csr(req.csr_pem.encode(), f"gateway:{gateway_id}")
    
    # Store Cert Subject in DB to bind it? (Optional, but good for revocation check)
    db_gw = await crud.get_gateway(db, gateway_id)
    if db_gw:
         # db_gw.cert_subject = ...
         # Update status
         db_gw.status = GatewayStatus.ACTIVE
         await db.commit()

    return {"certificate_pem": cert_pem.decode()}

class HeartbeatRequest(BaseModel):
    uptime_seconds: int
    local_ip: str
    agent_version: str
    timestamp: str

@app.post("/gateways/{gateway_id}/heartbeat")
async def heartbeat(
    gateway_id: str, 
    req: HeartbeatRequest, 
    db: AsyncSession = Depends(get_db)
):
    # TODO: Verify caller identity matches gateway_id via mTLS/Signer
    
    db_gw = await crud.get_gateway(db, gateway_id)
    if not db_gw:
        raise HTTPException(status_code=404, detail="Gateway not found")
        
    db_gw.last_seen = datetime.datetime.utcnow()
    # If it was OFFLINE/PROVISIONING, maybe set ACTIVE?
    if db_gw.status == GatewayStatus.OFFLINE:
         db_gw.status = GatewayStatus.ACTIVE
         
    await db.commit()
    return {"status": "ok"}

class IngestRecord(BaseModel):
    machine_id: str
    timestamp: datetime.datetime
    status: str
    metrics: Dict[str, Any]

@app.post("/ingest")
async def ingest_telemetry(
    records: List[Dict[str, Any]], 
    db: AsyncSession = Depends(get_db)
):
    received_count = len(records)
    print(f"Received {received_count} telemetry records")
    return {"status": "ok", "received": received_count}

# --- Driver Hub Endpoints ---
from .driver_hub import driver_hub as hub_service

class DriverResponse(BaseModel):
    driver_id: str
    version: str
    download_url: str
    shasum: str
    class Config:
        from_attributes = True

@app.on_event("startup")
async def seed_drivers():
    # Helper to seed drivers on startup
    async with AsyncSessionLocal() as db:
        await hub_service.seed_defaults(db)

@app.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    db: AsyncSession = Depends(get_db),
    # user: CurrentUser = Depends(get_user_with_roles) # Authenticated? Yes. Role? Viewer+
):
    # For now, allow open access or require auth
    # if not user: raise 401
    return await hub_service.get_drivers(db)

@app.get("/drivers/{driver_id}/{version}/download")
async def download_driver(
    driver_id: str, 
    version: str, 
    db: AsyncSession = Depends(get_db)
):
    meta = await hub_service.get_driver_version(db, driver_id, version)
    if not meta:
        raise HTTPException(status_code=404, detail="Driver version not found")
    
    # In real life, generate signed URL or redirect
    return {"url": meta.download_url}
