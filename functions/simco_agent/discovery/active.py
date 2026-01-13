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

def discover_active(subnets: List[str], ports: List[int], rate_limit_pps: int = 10) -> List[Dict[str, Any]]:
    """Performs a rate-limited active scan."""
    results = []
    if not subnets:
        return results

    logger.info(f"ActiveScan: Starting scan on {subnets} ports {ports} (RL={rate_limit_pps}pps)")
    
    nm = nmap.PortScanner()
    # Note: nmap itself doesn't have a direct 'pps' flag for simple scannng, 
    # but we can use timing templates or --min-rate / --max-rate
    scan_args = f"-Pn -p {','.join(map(str, ports))} --max-rate {rate_limit_pps}"
    
    try:
        for subnet in subnets:
            nm.scan(hosts=subnet, arguments=scan_args)
            for host in nm.all_hosts():
                if nm[host].state() == 'up':
                    # Only include if at least one port is open
                    for port in ports:
                        if nm[host].has_tcp(port) and nm[host]['tcp'][port]['state'] == 'open':
                            results.append({
                                "ip": host,
                                "source": "active_scan",
                                "port": port,
                                "confidence": 0.9
                            })
                            break
    except Exception as e:
        logger.error(f"ActiveScan: Error during nmap scan: {e}")

    logger.info(f"ActiveScan: Found {len(results)} targets")
    return results
