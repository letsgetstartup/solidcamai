import subprocess
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def discover_passive() -> List[Dict[str, Any]]:
    """Discovers neighbors passively by parsing the system ARP table."""
    candidates = []
    try:
        # Run 'ip neigh' or 'arp -a'
        output = subprocess.check_output(["ip", "neigh", "show"], stderr=subprocess.STDOUT, text=True)
        # Typical line: 192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
        lines = output.splitlines()
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                ip = parts[0]
                # Validate IP
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                    candidates.append({
                        "ip": ip,
                        "source": "passive_arp",
                        "confidence": 0.5 # Passive is lower confidence without probe
                    })
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("PassiveDiscovery: 'ip' command failed, trying 'arp -n'")
        try:
            output = subprocess.check_output(["arp", "-n"], stderr=subprocess.STDOUT, text=True)
            # Typical line: 192.168.1.1 (192.168.1.1) at aa:bb:cc:dd:ee:ff [ether] on eth0
            for line in output.splitlines():
                match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", line)
                if match:
                    candidates.append({
                        "ip": match.group(1),
                        "source": "passive_arp",
                        "confidence": 0.5
                    })
        except Exception as e:
            logger.error(f"PassiveDiscovery: Failed to run fallback arp command: {e}")

    logger.info(f"PassiveDiscovery: Found {len(candidates)} candidates")
    return candidates
