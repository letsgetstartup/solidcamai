from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Enum
from datetime import datetime
import enum

from .db import Base

class QRStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"

class MachineQRToken(Base):
    __tablename__ = "machine_qr_tokens"
    
    token_id = Column(String, primary_key=True)  # uuid
    machine_id = Column(String, nullable=False)  # matches MachineInfo.mac or internal ID
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    
    public_code = Column(String, unique=True, index=True, nullable=False) # The random token in the QR
    
    status = Column(Enum(QRStatusEnum), default=QRStatusEnum.ACTIVE, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=True) # user_id
    
    rotated_from_token_id = Column(String, ForeignKey("machine_qr_tokens.token_id"), nullable=True)
