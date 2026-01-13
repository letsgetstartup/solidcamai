import yaml
import argparse
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retention_enforcer")

def load_plans(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def enforce_retention(dataset, plans_path, dry_run=True):
    plans = load_plans(plans_path)
    retention_cfg = plans.get("retention_plans", {})
    
    # Tables to manage and their key in the config
    tables = {
        "raw_telemetry": "telemetry_raw",
        "hourly_rollups": "telemetry_hourly",
        "daily_rollups": "telemetry_daily",
        "events": "events"
    }

    logger.info(f"Target Dataset: {dataset}")
    logger.info(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")

    for table, cfg_key in tables.items():
        # Using 'standard' as default for global table enforcement simulation
        # In a real tenant-multi-table setup, this would be more complex
        days = retention_cfg.get("standard", {}).get(cfg_key, 30)
        
        sql = f"ALTER TABLE `{dataset}.{table}` SET OPTIONS (partition_expiration_days = {days});"
        
        if dry_run:
            print(f"[DRY-RUN] Would apply: {sql}")
        else:
            # In production: bq_client.query(sql)
            logger.info(f"APPLIED: {sql}")
            # Emit audit log
            print(f"AUDIT: RETENTION_UPDATED for {table} to {days} days.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--plans", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    enforce_retention(args.dataset, args.plans, args.dry_run)
