import os
import json
import hashlib
import requests
import shutil
import zipfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from simco_agent.config import settings
from simco_agent.security.signing import verify_driver_artifact
from simco_agent.security.identity import DeviceIdentity

class SyncManager:
    def __init__(self):
        self.cache_dir = settings.DRIVERS_CACHE_DIR
        self.active_dir = settings.DRIVERS_ACTIVE_DIR
        self.backup_dir = settings.DRIVERS_BACKUP_DIR
        self.manifest_url = settings.DRIVER_HUB_MANIFEST_URL
        self.registry_file = settings.MACHINE_REGISTRY_FILE
        self.pubkey_path = settings.DRIVER_PUBKEY_PATH
        self.identity = DeviceIdentity()
        
        # Ensure directories exist
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.active_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Helper to perform requests using device identity if configured."""
        return self.identity.secure_request(method, url, **kwargs)

    def fetch_manifest(self) -> Dict[str, Any]:
        """Fetch the driver hub manifest."""
        try:
            response = self._request("GET", self.manifest_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching manifest: {e}")
            return {"drivers": []}

    def get_required_drivers(self, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine which drivers are needed based on the machine registry."""
        if not os.path.exists(self.registry_file):
            return []

        with open(self.registry_file, "r") as f:
            registry = json.load(f)

        required_ids = set()
        for machine in registry:
            if "driver_id" in machine:
                required_ids.add(machine["driver_id"])
            elif "vendor" in machine:
                # Infer driver_id from vendor matches in manifest
                vendor = machine["vendor"].lower()
                for d in manifest.get("drivers", []):
                    if any(vendor in v.lower() for v in d.get("supported_vendors", [])):
                        required_ids.add(d["driver_id"])
                        break

        required_drivers = []
        for d in manifest.get("drivers", []):
            if d["driver_id"] in required_ids:
                required_drivers.append(d)
        
        return required_drivers

    def verify_sha256(self, file_path: str, expected_hash: str) -> bool:
        """Verify the SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest() == expected_hash

    def sync(self):
        """Execute the full sync process."""
        manifest = self.fetch_manifest()
        required = self.get_required_drivers(manifest)
        
        for driver in required:
            self._sync_driver(driver)

    def _sync_driver(self, driver: Dict[str, Any]):
        driver_id = driver["driver_id"]
        version = driver["version"]
        expected_hash = driver["sha256"]
        url = driver["url"]
        sig_url = f"{url}.sig"

        target_cache_path = os.path.join(self.cache_dir, f"{driver_id}_{version}.zip")
        target_sig_path = f"{target_cache_path}.sig"
        active_driver_dir = os.path.join(self.active_dir, driver_id)
        current_marker = os.path.join(active_driver_dir, "current")

        # 1. Check if already active and correct version
        if os.path.exists(current_marker):
            with open(os.path.join(current_marker, "metadata.json"), "r") as f:
                current_meta = json.load(f)
                if current_meta.get("version") == version and current_meta.get("sha256") == expected_hash:
                    return

        # 2. Download Artifact + Signature
        try:
            # Download ZIP
            if not os.path.exists(target_cache_path) or not self.verify_sha256(target_cache_path, expected_hash):
                print(f"Downloading {driver_id} v{version} artifact...")
                resp = self._request("GET", url, timeout=30)
                resp.raise_for_status()
                with open(target_cache_path, "wb") as f:
                    f.write(resp.content)
            
            # Download Signature
            print(f"Downloading {driver_id} v{version} signature...")
            resp_sig = self._request("GET", sig_url, timeout=10)
            resp_sig.raise_for_status()
            with open(target_sig_path, "wb") as f:
                f.write(resp_sig.content)
                
        except Exception as e:
            print(f"Download failed for {driver_id}: {e}")
            return

        # 3. VERIFY SIGNATURE (Task 7 Requirement: Fail Closed)
        print(f"Verifying signature for {driver_id}...")
        if not verify_driver_artifact(target_cache_path, target_sig_path, self.pubkey_path):
            print(f"CRITICAL: Signature verification FAILED for {driver_id}. Activation blocked.")
            # Emit event (mocked)
            from .buffer_manager import BufferManager
            BufferManager().enqueue({
                "machine_id": "EDGE_GATEWAY",
                "type": "UPDATE_BLOCKED",
                "severity": "CRITICAL",
                "details": {"driver_id": driver_id, "version": version, "reason": "signature_mismatch"}
            })
            return

        # 4. Hash Check Final
        if not self.verify_sha256(target_cache_path, expected_hash):
            print(f"Hash mismatch for {driver_id}")
            return

        # 5. Backup current active if it exists
        if os.path.exists(current_marker):
            backup_name = f"{driver_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            shutil.move(current_marker, os.path.join(self.backup_dir, backup_name))

        # 6. Activate
        print(f"Activating {driver_id} v{version}...")
        os.makedirs(active_driver_dir, exist_ok=True)
        with zipfile.ZipFile(target_cache_path, 'r') as zip_ref:
            zip_ref.extractall(current_marker)
        
        # Save verification metadata
        with open(os.path.join(current_marker, "metadata.json"), "w") as f:
            json.dump(driver, f)
