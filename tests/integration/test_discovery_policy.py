
import pytest
from unittest.mock import MagicMock, patch
from simco_agent.discovery.policy import DiscoveryPolicy
from simco_agent.discovery.active import discover_active
from simco_agent.discovery.orchestrator import DiscoveryOrchestrator

# Mock Nmap since we don't assume network access or root privileges in CI
@pytest.fixture
def mock_nmap():
    with patch("nmap.PortScanner") as mock:
        scanner = mock.return_value
        # Default behavior: host matches search, state up
        scanner.all_hosts.return_value = ["192.168.1.55"]
        scanner.__getitem__.return_value.state.return_value = "up"
        
        # Helper to simulate open ports
        def has_tcp(port):
            return port in [8193, 502] # Simulate Fanuc and Modbus open
        
        scanner.__getitem__.return_value.has_tcp.side_effect = has_tcp
        
        def tcp_info(port):
            if port in [8193, 502]:
                return {"state": "open"}
            return {"state": "closed"}
            
        scanner.__getitem__.return_value.__getitem__.side_effect = lambda key: tcp_info(int(key)) if key == 'tcp' else tcp_info(0) # simplified structure hack
        # The code does nm[host]['tcp'][port]['state']
        # Mock structure: nm[host] -> object with state() and ['tcp']
        
        host_mock = MagicMock()
        host_mock.state.return_value = "up"
        host_mock.has_tcp.side_effect = has_tcp
        host_mock.__getitem__.side_effect = lambda k: {8193: {"state": "open"}, 502: {"state": "open"}, 4840: {"state": "closed"}} if k == 'tcp' else None
        
        scanner.__getitem__.return_value = host_mock

        yield scanner

def test_policy_normalization():
    # Legacy list format
    p1 = DiscoveryPolicy(port_probes=[80, 443])
    normalized = p1.get_normalized_port_map()
    assert normalized == {"generic": [80, 443]}
    
    # Dict format
    p2 = DiscoveryPolicy(port_probes={"http": [80], "https": [443]})
    normalized2 = p2.get_normalized_port_map()
    assert normalized2 == {"http": [80], "https": [443]}

def test_active_discovery_mapping(mock_nmap):
    subnets = ["192.168.1.0/24"]
    port_map = {
        "fanuc_focas": [8193],
        "modbus": [502],
        "opcua": [4840]
    }
    
    results = discover_active(subnets, port_map)
    
    assert len(results) == 1
    target = results[0]
    assert target["ip"] == "192.168.1.55"
    
    # Check candidates
    candidates = target["protocol_candidates"]
    assert len(candidates) == 2
    
    # Find FOCAS
    focas = next((c for c in candidates if 8193 == c["port"]), None)
    assert focas is not None
    assert "fanuc_focas" in focas["protocols"]
    
    # Find Modbus
    modbus = next((c for c in candidates if 502 == c["port"]), None)
    assert modbus is not None
    assert "modbus" in modbus["protocols"]

def test_orchestrator_registry_update(mock_nmap, tmp_path):
    # Setup orchestrator with temp registry
    registry_file = tmp_path / "machine_registry.json"
    orch = DiscoveryOrchestrator(str(registry_file))
    
    # Override policy to use our map
    orch.policy.port_probes = {
        "fanuc_focas": [8193],
        "modbus": [502]
    }
    
    orch.run_discovery_cycle()
    
    # Check registry content
    import json
    with open(registry_file) as f:
        registry = json.load(f)
        
    assert len(registry) == 1
    machine = registry[0]
    assert machine["machine_id"] == "192.168.1.55"
    assert "metadata" in machine
    assert "protocols" in machine["metadata"]
    assert "fanuc_focas" in machine["metadata"]["protocols"]
    assert "modbus" in machine["metadata"]["protocols"]
