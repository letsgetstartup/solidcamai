from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Text, Integer
from datetime import datetime
import os
import enum

Base = declarative_base()

# --- Enums ---
class GatewayStatus(str, enum.Enum):
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    OFFLINE = "OFFLINE"

# --- Models ---
class Tenant(Base):
    __tablename__ = "tenants"
    tenant_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Site(Base):
    __tablename__ = "sites"
    site_id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    name = Column(String, nullable=False)
    timezone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Gateway(Base):
    __tablename__ = "gateways"
    gateway_id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    display_name = Column(String)
    serial = Column(String)
    cert_subject = Column(String, unique=True)
    status = Column(Enum(GatewayStatus), default=GatewayStatus.PROVISIONING)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String, nullable=False)
    actor_id = Column(String) # User ID or Gateway ID
    target_id = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True) # Auth Provider UID
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Membership(Base):
    __tablename__ = "memberships"
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), primary_key=True)
    site_id = Column(String, ForeignKey("sites.site_id"), primary_key=True, nullable=True) # If null, applies to all sites in tenant? Or use specific entries.
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    role = Column(Enum(UserRole), nullable=False)

class DriverMetadata(Base):
    __tablename__ = "driver_metadata"
    driver_id = Column(String, primary_key=True) # e.g. "mtconnect"
    version = Column(String, primary_key=True) # e.g. "1.0.0"
    download_url = Column(String, nullable=False)
    shasum = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DisplayDevice(Base):
    __tablename__ = "display_devices"
    display_id = Column(String, primary_key=True)
    tenant_id = Column(String, ForeignKey("tenants.tenant_id"), nullable=False)
    site_id = Column(String, ForeignKey("sites.site_id"), nullable=False)
    name = Column(String)
    token_hash = Column(String, unique=True, nullable=False)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Database Connection ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./control_plane.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
