from __future__ import annotations

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text
from datetime import datetime

from .db import Base

class ErpConnection(Base):
    __tablename__ = "erp_connections"
    id = Column(String, primary_key=True)                 # uuid
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    provider = Column(String, nullable=False)             # "sap_b1_service_layer"
    display_name = Column(String, nullable=False)

    # Connection details (non-secret)
    base_url = Column(String, nullable=False)
    company_db = Column(String, nullable=True)

    # Secrets stored externally; DB stores only reference
    secret_ref = Column(String, nullable=False)           # e.g. "sm://projects/.../secrets/..."
    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ErpEntityState(Base):
    __tablename__ = "erp_entity_state"
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(String, ForeignKey("erp_connections.id"), nullable=False)
    entity_name = Column(String, nullable=False)          # "items" / "production_orders" etc
    last_successful_sync_ts = Column(DateTime, nullable=True)
    last_source_updated_at_seen = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

class ErpMachineMap(Base):
    __tablename__ = "erp_machine_map"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    machine_id = Column(String, nullable=False)

    erp_system = Column(String, nullable=False)           # "sap_b1"
    erp_resource_code = Column(String, nullable=False)

    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)

    created_by_user_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
