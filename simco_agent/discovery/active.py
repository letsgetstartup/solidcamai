import logging
import time
import nmap
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def plan_active_scan(subnets: List[str], ports: List[int], dry_run: bool = False) -> Dict[str, Any]:
    """Generates a scan plan based on policy."""
    plan = {
        "targets": subnets,
        "ports": ports,
        "nmap_args": f"-Pn -p {','.join(map(str, ports))}"
    }
    if dry_run:
        logger.info(f"ActiveScan DRY-RUN: Targets={subnets}, Ports={ports}")
    return plan

def discover_active(subnets: List[str], port_map: Dict[str, List[int]], rate_limit_pps: int = 10) -> List[Dict[str, Any]]:
    """Performs a rate-limited active scan and maps open ports to protocols."""
    results = []
    if not subnets or not port_map:
        return results

    # Flatten all ports for the scan
    all_ports = set()
    port_to_protocols = {}
    
    for proto, ports in port_map.items():
        for p in ports:
            all_ports.add(p)
            if p not in port_to_protocols:
                port_to_protocols[p] = []
            port_to_protocols[p].append(proto)

    sorted_ports = sorted(list(all_ports))
    logger.info(f"ActiveScan: Starting scan on {subnets} ports {sorted_ports} (RL={rate_limit_pps}pps)")
    
    nm = nmap.PortScanner()
    scan_args = f"-Pn -p {','.join(map(str, sorted_ports))} --max-rate {rate_limit_pps}"
    
    try:
        for subnet in subnets:
            nm.scan(hosts=subnet, arguments=scan_args)
            for host in nm.all_hosts():
                if nm[host].state() == 'up':
                    # Check for open ports and map to protocols
                    candidates = []
                    for port in sorted_ports:
                        if nm[host].has_tcp(port) and nm[host]['tcp'][port]['state'] == 'open':
                            protos = port_to_protocols.get(port, ["unknown"])
                            candidates.append({
                                "port": port,
                                "protocols": protos
                            })
                    
                    if candidates:
                        results.append({
                            "ip": host,
                            "source": "active_scan",
                            "protocol_candidates": candidates,
                            "confidence": 0.5
                        })
    except Exception as e:
        logger.error(f"ActiveScan: Error during nmap scan: {e}")

    logger.info(f"ActiveScan: Found {len(results)} targets")
    return results
