import pytest
import pytest_asyncio
import os
import json
from simco_agent.db import init_agent_db, Base
from simco_agent.core.buffer_manager import buffer_manager
from simco_agent.core.uplink import UplinkWorker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # Patch DB for persistence test
    import simco_agent.db
    import simco_agent.core.buffer_manager
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    
    original_engine = simco_agent.db.engine
    original_session = simco_agent.db.AsyncSessionLocal
    original_buffer_session = simco_agent.core.buffer_manager.AsyncSessionLocal
    
    new_factory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    simco_agent.db.engine = test_engine
    simco_agent.db.AsyncSessionLocal = new_factory
    simco_agent.core.buffer_manager.AsyncSessionLocal = new_factory
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    await test_engine.dispose()
    simco_agent.db.engine = original_engine
    simco_agent.db.AsyncSessionLocal = original_session
    simco_agent.core.buffer_manager.AsyncSessionLocal = original_buffer_session

@pytest.mark.asyncio
async def test_buffer_persistence():
    # 1. Write Data
    payload = {"temp": 100, "machine": "m1"}
    await buffer_manager.write(payload)
    
    # 2. Read Batch
    batch = await buffer_manager.read_batch(10)
    assert len(batch) == 1
    loaded = json.loads(batch[0].payload_json)
    assert loaded["temp"] == 100
    
    # 3. Ack (Delete)
    await buffer_manager.ack_batch([batch[0].id])
    
    # 4. Verify Empty
    batch = await buffer_manager.read_batch(10)
    assert len(batch) == 0

@pytest.mark.asyncio
async def test_uplink_worker_flow():
    # Mock Client
    class MockClient:
        async def post_telemetry(self, records):
            return True
            
    worker = UplinkWorker(MockClient(), interval_seconds=0.1)
    
    # Fill Buffer
    await buffer_manager.write({"id": 1})
    await buffer_manager.write({"id": 2})
    
    # Run cycle once manually
    await worker._cycle()
    
    # Should be empty now
    batch = await buffer_manager.read_batch(10)
    assert len(batch) == 0
