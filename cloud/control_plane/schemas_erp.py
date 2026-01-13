from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List

class ErpConnectionCreate(BaseModel):
    provider: str = Field(..., examples=["sap_b1_service_layer"])
    display_name: str
    base_url: str
    company_db: Optional[str] = None
    username: str
    password: str
    verify_tls: bool = True

class ErpConnectionOut(BaseModel):
    id: str
    tenant_id: str
    provider: str
    display_name: str
    base_url: str
    company_db: Optional[str]
    enabled: bool

class ErpSyncRequest(BaseModel):
    entities: Optional[List[str]] = None  # None = all
    page_size: int = 200

class ErpMachineMapUpsert(BaseModel):
    site_id: str
    machine_id: str
    erp_system: str = "sap_b1"
    erp_resource_code: str
