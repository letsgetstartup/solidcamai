import os
import json
import hashlib
import argparse
from datetime import datetime

def compute_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_manifest(drivers_dir, base_url, out_path):
    manifest = {
        "manifest_version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "drivers": []
    }

    if not os.path.exists(drivers_dir):
        print(f"Error: Drivers directory {drivers_dir} not found.")
        return

    for driver_id in sorted(os.listdir(drivers_dir)):
        driver_path = os.path.join(drivers_dir, driver_id)
        if not os.path.isdir(driver_path):
            continue

        for version in sorted(os.listdir(driver_path)):
            version_path = os.path.join(driver_path, version)
            if not os.path.isdir(version_path):
                continue

            artifact_path = os.path.join(version_path, "driver.zip")
            metadata_path = os.path.join(version_path, "metadata.json")

            if not os.path.exists(artifact_path):
                print(f"Warning: No driver.zip found in {version_path}. Skipping.")
                continue

            # Load metadata
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)

            sha256 = compute_sha256(artifact_path)
            
            # Construct driver entry
            driver_entry = {
                "driver_id": driver_id,
                "version": version,
                "channel": metadata.get("channel", "prod"),
                "sha256": sha256,
                "url": f"{base_url.rstrip('/')}/{driver_id}/{version}/driver.zip",
                "entrypoint": metadata.get("entrypoint", "driver:Driver"),
                "supported_vendors": metadata.get("supported_vendors", []),
                "python": metadata.get("python", ">=3.11"),
                "artifact_path": artifact_path # For internal verification tests
            }
            manifest["drivers"].append(driver_entry)

    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest generated successfully at {out_path} with {len(manifest['drivers'])} drivers.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIMCO AI Driver Hub Manifest Generator")
    parser.params = parser.add_argument_group("Required")
    parser.add_argument("--drivers-dir", required=True, help="Path to drivers root directory")
    parser.add_argument("--base-url", required=True, help="Base URL for driver downloads")
    parser.add_argument("--out", required=True, help="Path to output manifest.json")
    
    args = parser.parse_args()
    generate_manifest(args.drivers_dir, args.base_url, args.out)
