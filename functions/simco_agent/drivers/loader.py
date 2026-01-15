import importlib.util
import hashlib
import logging
import os
import sys
from types import ModuleType
from typing import Optional
from simco_agent.drivers.common.models import DriverManifest

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    pass

class SecureDriverLoader:
    def __init__(self, drivers_root: str = None):
        # Default to simco_agent/drivers/impl if not specified
        if not drivers_root:
            base = os.path.dirname(os.path.abspath(__file__))
            self.drivers_root = os.path.join(base, "impl")
        else:
            self.drivers_root = drivers_root

    def load_driver(self, manifest: DriverManifest) -> ModuleType:
        """
        Loads a driver module securely by verifying its checksum.
        """
        # 1. Resolve File Path (Convention: name.replace('-', '_').py)
        # e.g. "haas-mtconnect" -> "haas_mtconnect.py"
        module_name = manifest.name.replace("-", "_")
        file_path = os.path.join(self.drivers_root, f"{module_name}.py")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Driver file not found: {file_path}")
            
        # 2. Verify Checksum (if present in manifest)
        if manifest.checksum:
            file_hash = self._compute_sha256(file_path)
            if file_hash != manifest.checksum:
                logger.critical(f"Security Alert: Checksum mismatch for {manifest.name}. Expected {manifest.checksum}, got {file_hash}")
                raise SecurityError(f"Checksum mismatch for driver {manifest.name}")
            logger.info(f"Integrity verified for {manifest.name}")
        else:
            logger.warning(f"Loading driver {manifest.name} WITHOUT checksum verification (Not Recommended for Prod)")

        # 3. Load Module
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
            else:
                raise ImportError(f"Could not load spec for {file_path}")
        except Exception as e:
            logger.error(f"Failed to load driver module {module_name}: {e}")
            raise

    def _compute_sha256(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash string value in blocks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
