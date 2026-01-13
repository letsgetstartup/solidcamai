import pytest
import multiprocessing
import uvicorn
import time
import requests
import os
import shutil
import asyncio
from cloud.control_plane.app import app
# We need to run the agent in a way that uses the mocked or real components
from simco_agent.core.uplink import UplinkWorker
from simco_agent.core.buffer_manager import buffer_manager

# Configuration
API_PORT = 9991
API_URL = f"http://localhost:{API_PORT}"

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=API_PORT, log_level="error")

@pytest.fixture(scope="module")
def api_server():
    proc = multiprocessing.Process(target=run_server, daemon=True)
    proc.start()
    # Wait for server
    for _ in range(50):
        try:
            requests.get(f"{API_URL}/health")
            break
        except:
            time.sleep(0.1)
    else:
        raise RuntimeError("Server failed to start")
    
    yield
    proc.terminate()

@pytest.fixture
def agent_config():
    # Setup temp DB
    os.environ["AGENT_DB_PATH"] = "e2e_gateway.db"
    
    # Init DB (need to do this in the test process)
    # But since we are mocking the UplinkWorker flow, we might strictly 
    # use the modules.
    
    # CLEANUP
    if os.path.exists("e2e_gateway.db"):
        os.remove("e2e_gateway.db")
        
    yield
    
    if os.path.exists("e2e_gateway.db"):
        os.remove("e2e_gateway.db")

@pytest.mark.asyncio
async def test_e2e_uplink(api_server, agent_config):
    # This test verifies: Agent Buffer -> Uplink -> Cloud API
    
    # 1. Initialize Agent DB (imports will pick up env var)
    from simco_agent.db import init_agent_db
    await init_agent_db()
    
    # 2. Setup Agent Components
    # We need a client that talks to the real local server
    class RealClient:
        async def post_telemetry(self, records):
            url = f"{API_URL}/ingest"
            # In a real async client we'd use httpx
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=records)
                resp.raise_for_status()
                return True

    worker = UplinkWorker(RealClient(), interval_seconds=0.1)
    
    # 3. Simulate Data Generation (Agent)
    telemetry = [
        {"machine_id": "m1", "temp": 100, "ts": "2024-01-01T12:00:00Z"},
        {"machine_id": "m1", "temp": 101, "ts": "2024-01-01T12:00:01Z"}
    ]
    
    for t in telemetry:
        await buffer_manager.write(t)
        
    # Verify buffer has data
    batch = await buffer_manager.read_batch()
    assert len(batch) >= 2
    
    # 4. Agent Uplink Cycle
    await worker._cycle() # Should read 2 items, send to API 9991, ack 2 items
    
    # 5. Verify Buffer Empty (Ack successful)
    batch = await buffer_manager.read_batch()
    assert len(batch) == 0
    
    # 6. Verify Server Side?
    # Since we are running the server in a separate process, we can't easily inspect its memory.
    # But if `worker._cycle()` didn't throw and emptied the buffer, 
    # it means the API returned 200 OK.
    # We can rely on that for this level of E2E.
