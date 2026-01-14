from google.cloud import bigquery
import os

PROJECT_ID = "solidcamal"
DATASET_ID = "simco_telemetry"

def create_views():
    client = bigquery.Client(project=PROJECT_ID)
    
    views = [
        "sql/views/erp_production_orders_latest.sql",
        "sql/views/site_orders_now.sql"
    ]
    
    for view_file in views:
        with open(view_file, "r") as f:
            sql = f.read()
            # Replace placeholder dataset if needed, but the files seem to use simco_telemetry.
            # We should probably make it robust by replacing simco_telemetry with the actual dataset.
            sql = sql.replace("`simco_telemetry.", f"`{PROJECT_ID}.{DATASET_ID}.")
            
            print(f"Creating view from {view_file}...")
            try:
                query_job = client.query(sql)
                query_job.result()
                print(f"OK: {view_file}")
            except Exception as e:
                print(f"ERROR creating view from {view_file}: {e}")

if __name__ == "__main__":
    create_views()
