import pytest
import datetime
from cloud.control_plane.timeseries import TelemetryHypertable, ts_service
from cloud.control_plane.db import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import pytest_asyncio

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        
    await engine.dispose()

@pytest.mark.asyncio
async def test_timeseries_ingest(db_session):
    records = [
        {
            "machine_id": "m1", 
            "timestamp": "2024-01-01T10:00:00Z", 
            "metrics": {"temp": 100.5, "load": 50}
        }
    ]
    
    await ts_service.write_batch(db_session, records)
    
    # Query back
    rows = await ts_service.query_metrics(db_session, "m1", "temp")
    assert len(rows) == 1
    assert rows[0].metric_value == 100.5
    
    rows_load = await ts_service.query_metrics(db_session, "m1", "load")
    assert len(rows_load) == 1
    assert rows_load[0].metric_value == 50.0

@pytest.mark.asyncio
async def test_timeseries_parsing(db_session):
    # Test with existing datetime obj vs string
    now = datetime.datetime.utcnow()
    records = [
        {"machine_id": "m2", "timestamp": now, "metrics": {"a": 1}}
    ]
    await ts_service.write_batch(db_session, records)
    
    rows = await ts_service.query_metrics(db_session, "m2", "a")
    assert len(rows) == 1
    # Check close enough timestamp?
    # assert rows[0].timestamp == now # Might fail slightly due to DB precision, but roughly.
    assert abs((rows[0].timestamp - now).total_seconds()) < 1.0
