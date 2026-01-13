from __future__ import annotations

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .models_qr import QRStatusEnum

class MachineQRTokenOut(BaseModel):
    token_id: str
    machine_id: str
    tenant_id: str
    site_id: str
    public_code: str
    deep_link: str
    status: QRStatusEnum
    created_at: datetime
    
class QRGenerateRequest(BaseModel):
    machine_id: str
    site_id: str # Confirm site context

class QRRotateRequest(BaseModel):
    reason: Optional[str] = None
