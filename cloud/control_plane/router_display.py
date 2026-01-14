from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .db import get_db, DisplayDevice
from pydantic import BaseModel
import uuid
import secrets
import hashlib
from datetime import datetime

router = APIRouter(prefix="/displays", tags=["Displays"])

class DisplayCreate(BaseModel):
    tenant_id: str
    site_id: str
    name: str

class DisplayResponse(BaseModel):
    display_id: str
    tenant_id: str
    site_id: str
    name: str
    token: str = None # Only returned on creation
    enabled: bool

@router.post("", response_model=DisplayResponse)
async def create_display(req: DisplayCreate, db: AsyncSession = Depends(get_db)):
    display_id = str(uuid.uuid4())
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    new_display = DisplayDevice(
        display_id=display_id,
        tenant_id=req.tenant_id,
        site_id=req.site_id,
        name=req.name,
        token_hash=token_hash,
        enabled=1
    )
    db.add(new_display)
    await db.commit()
    
    return DisplayResponse(
        display_id=display_id,
        tenant_id=req.tenant_id,
        site_id=req.site_id,
        name=req.name,
        token=token,
        enabled=True
    )

@router.get("/{display_id}", response_model=DisplayResponse)
async def get_display(display_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DisplayDevice).where(DisplayDevice.display_id == display_id))
    display = res.scalars().first()
    if not display:
        raise HTTPException(status_code=404, detail="Display not found")
    
    return DisplayResponse(
        display_id=display.display_id,
        tenant_id=display.tenant_id,
        site_id=display.site_id,
        name=display.name,
        enabled=bool(display.enabled)
    )
