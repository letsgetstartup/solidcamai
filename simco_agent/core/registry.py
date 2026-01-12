import json
import os
import logging
from typing import List, Dict, Any
from simco_common.schemas_v3 import MachineRegistryEntry
from simco_agent.config import settings

logger = logging.getLogger("simco_agent.registry")

def load_registry(path: str = None) -> List[Dict[str, Any]]:
    path = path or settings.MACHINE_REGISTRY_FILE
    if not os.path.exists(path):
        return []

    with open(path, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return []

    # Migration: if data is a dict (legacy), convert to list
    if isinstance(data, dict):
        logger.info("Migrating machine_registry from dict to list format.")
        migrated = []
        for ip, entry in data.items():
            if isinstance(entry, dict):
                # Ensure it has the required fields
                if "ip" not in entry:
                    entry["ip"] = ip
                if "machine_id" not in entry:
                    entry["machine_id"] = ip
                migrated.append(entry)
        # Save migrated version
        save_registry(migrated, path)
        return migrated

    return data if isinstance(data, list) else []

def save_registry(entries: List[Dict[str, Any]], path: str = None):
    path = path or settings.MACHINE_REGISTRY_FILE
    with open(path, "w") as f:
        json.dump(entries, f, indent=2)
