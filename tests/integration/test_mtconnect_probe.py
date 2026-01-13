import pytest
import asyncio
from typing import AsyncGenerator
from tests.simulators.mtconnect_server import MTConnectSimulator
from simco_agent.discovery.probes.mtconnect_probe import MTConnectProbe
from simco_agent.discovery.fingerprinting import FingerprintOrchestrator

import pytest_asyncio

@pytest_asyncio.fixture
async def mtconnect_server() -> AsyncGenerator[MTConnectSimulator, None]:
    # Use a non-standard port to avoid conflicts
    server = MTConnectSimulator(port=17878)
    await server.start()
    yield server
    await server.stop()

@pytest.mark.asyncio
async def test_mtconnect_probe_direct(mtconnect_server):
    probe = MTConnectProbe()
    fp = await probe.run("127.0.0.1", 17878)
    
    assert fp is not None
    assert fp.protocol == "mtconnect"
    assert fp.vendor == "Haas Automation"
    assert fp.model == "VF-2"
    assert fp.serial == "123456"
    assert fp.confidence >= 0.9

@pytest.mark.asyncio
async def test_fingerprint_orchestrator_dispatch(mtconnect_server):
    orch = FingerprintOrchestrator()
    candidates = [{
        "ip": "127.0.0.1",
        "protocol_candidates": [{"port": 17878, "protocols": ["mtconnect"]}]
    }]
    
    results = await orch.run(candidates)
    assert len(results) == 1
    fp = results[0]
    assert fp.protocol == "mtconnect"
    assert fp.vendor == "Haas Automation"
