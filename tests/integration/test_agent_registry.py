import pytest
import asyncio
import os
import json
from simco_agent.core.registry import registry
from simco_agent.db import init_agent_db, Base, engine
from simco_agent.schemas import MachineInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

import pytest_asyncio

# Use a test DB file
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory DB
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # 1. Create fresh engine for this test
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    
    # 2. Patch the global engine and session factory in the module
    import simco_agent.db
    import simco_agent.core.registry
    
    original_engine = simco_agent.db.engine
    original_session = simco_agent.db.AsyncSessionLocal
    original_registry_session = simco_agent.core.registry.AsyncSessionLocal
    
    new_session_factory = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    simco_agent.db.engine = test_engine
    simco_agent.db.AsyncSessionLocal = new_session_factory
    simco_agent.core.registry.AsyncSessionLocal = new_session_factory
    
    # 3. Init DB
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    # 4. Cleanup
    await test_engine.dispose()
    
    # Restore (optional but good hygiene)
    simco_agent.db.engine = original_engine
    simco_agent.db.AsyncSessionLocal = original_session
    simco_agent.core.registry.AsyncSessionLocal = original_registry_session
    
    if os.path.exists("machine_registry.json"):
        os.remove("machine_registry.json")
    if os.path.exists("machine_registry.json"):
        os.remove("machine_registry.json")
    if os.path.exists("machine_registry.json.bak"):
        os.remove("machine_registry.json.bak")

@pytest.mark.asyncio
async def test_migration_and_retrieval():
    # 1. Create Legacy JSON
    legacy_data = [
        {"mac": "AA:BB:CC:DD:EE:FF", "ip": "192.168.1.100", "protocol": "fanuc", "name": "Legacy CNC 1"}
    ]
    with open("machine_registry.json", "w") as f:
        json.dump(legacy_data, f)
        
    # 2. Run Migration
    await registry.migrate_legacy_registry()
    
    # 3. Verify Enrolled
    machines = await registry.get_enrolled_machines()
    assert len(machines) == 1
    assert machines[0].mac == "AA:BB:CC:DD:EE:FF"
    assert machines[0].vendor == "FANUC"
    
    # 4. Verify JSON renamed
    assert not os.path.exists("machine_registry.json")
    assert os.path.exists("machine_registry.json.bak")

@pytest.mark.asyncio
async def test_discovery_flow():
    # 1. Register Discovered
    info = MachineInfo(mac="11:22:33:44:55:66", ip="10.0.0.5", vendor="SIEMENS")
    await registry.register_discovered_machine(info)
    
    # Should NOT be returned in enrolled yet
    enrolled = await registry.get_enrolled_machines()
    assert len(enrolled) == 0
    
    # 2. Enroll
    await registry.enroll_machine(info.mac, "My Siemens", "siemens-opcua")
    
    # 3. Verify
    enrolled = await registry.get_enrolled_machines()
    assert len(enrolled) == 1
    assert enrolled[0].driver_id == "siemens-opcua"
