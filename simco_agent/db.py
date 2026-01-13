from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import datetime
import enum
import os

Base = declarative_base()

class MachineStatus(str, enum.Enum):
    DISCOVERED = "DISCOVERED"
    ENROLLED = "ENROLLED"
    DISABLED = "DISABLED"

class Machine(Base):
    __tablename__ = "machines"
    mac = Column(String, primary_key=True)
    ip = Column(String)
    name = Column(String)
    vendor = Column(String)
    protocol = Column(String)
    driver_id = Column(String, nullable=True)
    status = Column(Enum(MachineStatus), default=MachineStatus.DISCOVERED)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class TelemetryBuffer(Base):
    __tablename__ = "telemetry_buffer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    payload_json = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Ensure data directory exists
DB_PATH = os.environ.get("AGENT_DB_PATH", "gateway.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_agent_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
