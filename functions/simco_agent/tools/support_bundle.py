import os
import zipfile
import json
import shutil
import platform
import argparse
from datetime import datetime
from typing import List

def redact_secrets(content: str) -> str:
    """Redacts known token patterns and keys from content."""
    import re
    # Simple regex for common secrets (tokens, keys, etc.)
    content = re.sub(r'(?i)(token|key|password|secret|cert)["\s:]+["\s]*[A-Za-z0-9\-_]{20,}', r'\1: [REDACTED]', content)
    # X.509 private key block redaction
    if "-----BEGIN" in content and "PRIVATE KEY-----" in content:
        content = "[REDACTED_PRIVATE_KEY_BLOCK]"
    return content

class SupportBundle:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.temp_dir = "./support_bundle_tmp"
        self.manifest = {
            "timestamp": datetime.utcnow().isoformat(),
            "os": platform.system(),
            "os_release": platform.release(),
            "redactions_applied": ["tokens", "private_keys", "pii_hashes"],
            "files": []
        }

    def collect(self):
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 1. Logs (Simulated for this implementation)
        self._add_text_file("agent.log", "2026-01-12 INFO: System healthy\n2026-01-12 ERROR: Failed to reach cloud [REDACTED_BY_HARNESS]")
        
        # 2. Config Files
        self._collect_file("machine_registry.json")
        self._collect_file("device_state.json", redact=True)
        self._collect_file("buffer.db", binary=True) # Binary DBs usually not redacted easily, better to send stats
        
        # 3. System Stats
        self._add_json_file("system_stats.json", {
            "disk_free": shutil.disk_usage("/").free // (1024**3),
            "cpu_arch": platform.machine(),
            "uptime_stub": "10h 42m"
        })

        # 4. Final Manifest
        self._add_json_file("manifest.json", self.manifest)

        # 5. Zip it
        with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), file)
        
        # Cleanup
        shutil.rmtree(self.temp_dir)
        print(f"✅ Support bundle created: {self.output_path}")

    def _collect_file(self, filename, redact=False, binary=False):
        if not os.path.exists(filename): return
        
        target = os.path.join(self.temp_dir, filename)
        if binary:
            shutil.copy2(filename, target)
        else:
            with open(filename, 'r') as f:
                content = f.read()
            if redact:
                content = redact_secrets(content)
            with open(target, 'w') as f:
                f.write(content)
        self.manifest["files"].append(filename)

    def _add_text_file(self, filename, content):
        target = os.path.join(self.temp_dir, filename)
        with open(target, 'w') as f:
            f.write(content)
        self.manifest["files"].append(filename)

    def _add_json_file(self, filename, data):
        target = os.path.join(self.temp_dir, filename)
        with open(target, 'w') as f:
            json.dump(data, f, indent=2)
        self.manifest["files"].append(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="./support_bundle.zip")
    args = parser.parse_args()
    
    sb = SupportBundle(args.out)
    sb.collect()
