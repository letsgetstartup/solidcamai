import hashlib
import json
from typing import Optional
from simco_agent.drivers.common.models import Fingerprint

def generate_machine_id(fp: Fingerprint) -> str:
    """
    Generates a deterministic Machine ID based on fingerprint data.
    If serial/uuid is present, uses that (strong identity).
    Otherwise falls back to IP + Protocol (weak identity).
    """
    if fp.serial:
        # Strong identity: UUID/Serial provided by device
        raw = f"serial:{fp.serial}"
    elif fp.vendor and fp.model:
        # Medium identity: Vendor + Model + IP (likely stable for fix deployment)
        raw = f"{fp.vendor}:{fp.model}:{fp.ip}"
    else:
        # Weak identity: IP + Protocol
        raw = f"{fp.ip}:{fp.protocol}"
        
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
