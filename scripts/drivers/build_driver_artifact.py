import os
import zipfile
import argparse
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_driver")

def build_artifact(driver_id, version, channel="dev"):
    src_dir = os.path.join("drivers_src", driver_id)
    out_dir = os.path.join("driver_hub", "drivers", driver_id, version)
    os.makedirs(out_dir, exist_ok=True)

    zip_path = os.path.join(out_dir, "driver.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(src_dir):
            if "tests" in root or "sims" in root:
                continue # Skip tests and sims in artifact
            for file in files:
                if file.endswith(".yaml") or file.endswith(".py") or file.endswith(".txt"):
                    rel_path = os.path.relpath(os.path.join(root, file), src_dir)
                    zipf.write(os.path.join(root, file), rel_path)

    logger.info(f"Successfully built {zip_path}")

    # Create metadata.json for the manifest generator
    import yaml
    import json
    meta_src = os.path.join(src_dir, "metadata.yaml")
    if os.path.exists(meta_src):
        with open(meta_src, "r") as f:
            meta = yaml.safe_load(f)
        
        hub_meta = {
            "driver_id": driver_id,
            "version": version,
            "channel": channel,
            "entrypoint": "driver:FanucDriver", # Simplified
            "supported_vendors": [meta.get("vendor")],
            "python": ">=3.11"
        }
        meta_out = os.path.join(out_dir, "metadata.json")
        with open(meta_out, "w") as f:
            json.dump(hub_meta, f, indent=2)
        logger.info(f"Generated {meta_out}")

    return zip_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--driver_id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", default="dev")
    args = parser.parse_args()
    build_artifact(args.driver_id, args.version, args.channel)
