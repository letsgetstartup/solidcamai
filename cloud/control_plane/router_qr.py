from __future__ import annotations

import uuid
import secrets
import io
import base64
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .db import get_db
from .models_qr import MachineQRToken, QRStatusEnum
from .schemas_qr import MachineQRTokenOut, QRGenerateRequest, QRRotateRequest

# Try to import qrcode
try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

router = APIRouter(tags=["qr"])

DOMAIN = "https://portal.simco.ai" # Should come from config

def _generate_public_code() -> str:
    # 12 chars base32-like (alphanumeric uppercase, no ambiguous chars if possible)
    # Using secrets.token_hex(6).upper() -> 12 chars
    return secrets.token_hex(6).upper()

def _get_deep_link(code: str) -> str:
    return f"{DOMAIN}/m/{code}"

@router.post("/mgmt/v1/sites/{site_id}/machines/{machine_id}/qr", response_model=MachineQRTokenOut)
async def get_or_create_qr(
    site_id: str, 
    machine_id: str, 
    tenant_id: str, # passed via query or dep in real app, here explicit for simplicity
    db: AsyncSession = Depends(get_db)
):
    # Check for existing ACTIVE token
    stmt = select(MachineQRToken).where(
        MachineQRToken.site_id == site_id,
        MachineQRToken.machine_id == machine_id,
        MachineQRToken.status == QRStatusEnum.ACTIVE
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        return MachineQRTokenOut(
            token_id=existing.token_id,
            machine_id=existing.machine_id,
            tenant_id=existing.tenant_id,
            site_id=existing.site_id,
            public_code=existing.public_code,
            deep_link=_get_deep_link(existing.public_code),
            status=existing.status,
            created_at=existing.created_at
        )
        
    # Create new
    code = _generate_public_code()
    new_token = MachineQRToken(
        token_id=str(uuid.uuid4()),
        machine_id=machine_id,
        tenant_id=tenant_id,
        site_id=site_id,
        public_code=code,
        status=QRStatusEnum.ACTIVE,
        created_at=datetime.utcnow(),
        created_by="admin" # In real RBAC, get from current_user
    )
    db.add(new_token)
    await db.commit()
    
    return MachineQRTokenOut(
        token_id=new_token.token_id,
        machine_id=new_token.machine_id,
        tenant_id=new_token.tenant_id,
        site_id=new_token.site_id,
        public_code=new_token.public_code,
        deep_link=_get_deep_link(new_token.public_code),
        status=new_token.status,
        created_at=new_token.created_at
    )

@router.get("/mgmt/v1/sites/{site_id}/machines/{machine_id}/qr/label")
async def get_qr_label(site_id: str, machine_id: str, tenant_id: str, db: AsyncSession = Depends(get_db)):
    # Get ACTIVE code
    stmt = select(MachineQRToken).where(
        MachineQRToken.site_id == site_id,
        MachineQRToken.machine_id == machine_id,
        MachineQRToken.status == QRStatusEnum.ACTIVE
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    
    if not token:
        # Auto-create? Or 404. Let's 404 to ensure explicit creation.
        raise HTTPException(404, "No active QR token found. Generate one first.")
        
    link = _get_deep_link(token.public_code)
    
    if not HAS_QRCODE:
        return Response(content="qrcode library not installed", status_code=501)
        
    # Generate QR Image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H, # High error correction
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to BytesIO
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return Response(content=buf.read(), media_type="image/png")

@router.get("/mobile/v1/machines/by-token/{public_code}/context")
async def resolve_machine_context(public_code: str, db: AsyncSession = Depends(get_db)):
    # In real app: Verify User Auth first!
    
    stmt = select(MachineQRToken).where(MachineQRToken.public_code == public_code)
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    
    if not token:
        raise HTTPException(404, "Invalid or unknown machine code")
        
    if token.status != QRStatusEnum.ACTIVE:
        raise HTTPException(403, "This QR code has been revoked")
        
    # Return context
    return {
        "machine_id": token.machine_id,
        "site_id": token.site_id,
        "tenant_id": token.tenant_id,
        "machine_name": f"Machine {token.machine_id}", # Lookup real name
        "status": "IDLE", # Real lookup
        "allowed_actions": ["downtime", "quality", "maintenance"]
    }
