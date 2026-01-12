import os
import yaml
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compat_matrix")

def generate_matrix():
    src_dir = "drivers_src"
    matrix = []

    if not os.path.exists(src_dir):
        logger.error(f"Source directory {src_dir} does not exist.")
        return

    for driver_id in os.listdir(src_dir):
        meta_path = os.path.join(src_dir, driver_id, "metadata.yaml")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                try:
                    meta = yaml.safe_load(f)
                    matrix.append(meta)
                except Exception as e:
                    logger.error(f"Failed to parse {meta_path}: {e}")

    # 1. Generate JSON
    with open("docs/compatibility_matrix.json", "w") as f:
        json.dump(matrix, f, indent=2)
    logger.info("Generated docs/compatibility_matrix.json")

    # 2. Generate Markdown
    with open("docs/compatibility_matrix.md", "w") as f:
        f.write("# SIMCO AI Driver Compatibility Matrix\n\n")
        f.write("| Driver ID | Version | Vendor | Protocol | Supported Models |\n")
        f.write("|-----------|---------|--------|----------|------------------|\n")
        for m in matrix:
            models = ", ".join(m.get("supported_models", []))
            f.write(f"| {m['driver_id']} | {m['version']} | {m['vendor']} | {m['protocol']} | {models} |\n")
    logger.info("Generated docs/compatibility_matrix.md")

if __name__ == "__main__":
    generate_matrix()
