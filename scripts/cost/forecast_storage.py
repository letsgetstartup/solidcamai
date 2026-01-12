import argparse
import json
import os

def forecast_storage(sites, machines_per_site, sample_seconds, avg_bytes, plan, out_path):
    # Retention (days) based on plan
    plans = {
        "pilot": {"raw": 30, "hourly": 180, "daily": 730},
        "standard": {"raw": 90, "hourly": 365, "daily": 1095},
        "enterprise": {"raw": 180, "hourly": 730, "daily": 1825}
    }
    
    cfg = plans.get(plan, plans["standard"])
    
    total_machines = sites * machines_per_site
    records_per_day_per_machine = (24 * 3600) / sample_seconds
    total_records_per_day = total_machines * records_per_day_per_machine
    
    # 1. Raw Storage (Daily GB)
    daily_raw_gb = (total_records_per_day * avg_bytes) / (1024**3)
    monthly_raw_gb = daily_raw_gb * 30
    
    # 2. Rollup Storage (Approximation: Hourly=1/360, Daily=1/24 of Hourly)
    daily_rollup_gb = (daily_raw_gb / 360) + (daily_raw_gb / (360 * 24))
    monthly_rollup_gb = daily_rollup_gb * 30

    results = {
        "parameters": {
            "sites": sites,
            "machines": total_machines,
            "sample_seconds": sample_seconds,
            "avg_bytes": avg_bytes,
            "plan": plan
        },
        "daily_raw_gb": round(daily_raw_gb, 2),
        "monthly_raw_gb": round(monthly_raw_gb, 2),
        "monthly_rollup_gb": round(monthly_rollup_gb, 4),
        "estimated_monthly_cost_usd": round(monthly_raw_gb * 0.02, 2) # $0.02 per GB active storage
    }

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    # Markdown doc
    doc_path = os.path.join(os.path.dirname(out_path), "..", "docs", "cost_forecast.md")
    os.makedirs(os.path.dirname(doc_path), exist_ok=True)
    with open(doc_path, "w") as f:
        f.write("# SIMCO AI Storage Cost Forecast\n\n")
        f.write(f"**Scenario**: {sites} sites with {machines_per_site} machines each.\n")
        f.write(f"**Plan**: {plan.upper()}\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total Machines | {total_machines} |\n")
        f.write(f"| Monthly Raw Ingestion (GB) | {results['monthly_raw_gb']} |\n")
        f.write(f"| Monthly Rollup Storage (GB) | {results['monthly_rollup_gb']} |\n")
        f.write(f"| Estimated Storage Cost (USD/mo) | ${results['estimated_monthly_cost_usd']} |\n")

    print(f"Forecast generated: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sites", type=int, default=22000)
    parser.add_argument("--machines-per-site", type=int, default=20)
    parser.add_argument("--sample-seconds", type=int, default=5)
    parser.add_argument("--avg-bytes-per-record", type=int, default=600)
    parser.add_argument("--plan", default="standard")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    
    forecast_storage(args.sites, args.machines_per_site, args.sample_seconds, args.avg_bytes_per_record, args.plan, args.out)
