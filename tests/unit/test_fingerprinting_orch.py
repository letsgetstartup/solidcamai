
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from simco_agent.discovery.fingerprinting import FingerprintOrchestrator
from simco_agent.drivers.common.models import Fingerprint
from simco_agent.discovery.orchestrator import DiscoveryOrchestrator

@pytest.mark.asyncio
async def test_fingerprint_orchestrator_run():
    orch = FingerprintOrchestrator()
    
    candidates = [
        {
            "ip": "1.2.3.4",
            "protocol_candidates": [
                {"port": 8193, "protocols": ["fanuc_focas"]}
            ]
        },
        {
            "ip": "5.6.7.8",
            "protocol_candidates": [] # No hints
        }
    ]
    
    results = await orch.run(candidates)
    
    # Second candidate skipped (no hints)
    assert len(results) == 1
    fp = results[0]
    assert fp.ip == "1.2.3.4"
    assert fp.protocol == "fanuc_focas"
    assert fp.evidence["port_open"] == 8193

@pytest.mark.asyncio
async def test_orchestrator_integration(tmp_path):
    # Setup orchestrator with temp registry
    registry_file = tmp_path / "machine_registry.json"
    orch = DiscoveryOrchestrator(str(registry_file))
    
    # 1. Create a machine entry (simulating discovery)
    orch._update_registry([{
        "ip": "1.2.3.4", 
        "source": "active", 
        "protocol_candidates": [{"port": 8193, "protocols": ["fanuc_focas"]}]
    }])
    
    # 2. Run fingerprinting integration
    candidates = [{
        "ip": "1.2.3.4",
        "protocol_candidates": [{"port": 8193, "protocols": ["fanuc_focas"]}]
    }]
    
    fps = await orch.run_fingerprinting(candidates)
    assert len(fps) == 1
    
    # 3. Save fingerprints
    orch.save_fingerprints(fps)
    
    # 4. Verify registry update
    import json
    with open(registry_file) as f:
        data = json.load(f)
        
    entry = data[0]
    assert entry["ip"] == "1.2.3.4"
    assert "metadata" in entry
    assert "fingerprint" in entry["metadata"]
    assert entry["metadata"]["fingerprint"]["protocol"] == "fanuc_focas"
