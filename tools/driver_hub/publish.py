import os
import subprocess
import argparse
import sys

def run_manifest_gen(drivers_dir, base_url, out):
    cmd = [
        sys.executable, "-m", "tools.driver_hub.generate_manifest",
        "--drivers-dir", drivers_dir,
        "--base-url", base_url,
        "--out", out
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def publish_gcs(bucket_name, source_dir):
    try:
        # Check if bucket exists
        subprocess.run(["gcloud", "storage", "buckets", "describe", f"gs://{bucket_name}"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print(f"Error: Bucket gs://{bucket_name} does not exist or access denied.")
        return

    # Sync files
    cmd = ["gcloud", "storage", "rsync", source_dir, f"gs://{bucket_name}", "--recursive"]
    print(f"Publishing to GCS: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Successfully published to gs://{bucket_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SIMCO AI Driver Hub Publisher")
    parser.add_argument("--drivers-dir", default="driver_hub/drivers", help="Local drivers directory")
    parser.add_argument("--base-url", required=True, help="Base URL for drivers (http or gs)")
    parser.add_argument("--out", default="driver_hub/manifest.json", help="Path to manifest.json")
    parser.add_argument("--gcs-bucket", help="Optional GCS bucket to publish to (e.g., simco-driver-hub)")
    
    args = parser.parse_args()
    
    # Always generate manifest locally first
    run_manifest_gen(args.drivers_dir, args.base_url, args.out)
    
    # Optionally publish to GCS
    if args.gcs_bucket:
        # Note: manifest.json is typically at driver_hub/manifest.json
        # and drivers are at driver_hub/drivers/
        # We publish the whole driver_hub directory
        hub_root = os.path.dirname(args.out)
        publish_gcs(args.gcs_bucket, hub_root)
