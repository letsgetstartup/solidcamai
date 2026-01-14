from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import os

PROJECT_ID = "solidcamal"
DATASET_ID = "simco_telemetry"

def init_bq():
    client = bigquery.Client(project=PROJECT_ID)

    # 1. Create Dataset
    dataset_ref = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_ref} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {dataset_ref}.")

    # 2. Create raw_telemetry Table
    table_id = f"{dataset_ref}.raw_telemetry"
    schema_telemetry = [
        bigquery.SchemaField("record_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("device_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"), # Keeping as STRING for ISO8601 compat
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("metrics", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("ip", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("vendor", "STRING", mode="NULLABLE"),
    ]
    create_table_if_not_exists(client, table_id, schema_telemetry)

    # 3. Create raw_events Table
    table_id = f"{dataset_ref}.raw_events"
    schema_events = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("details", "JSON", mode="NULLABLE"),
    ]
    create_table_if_not_exists(client, table_id, schema_events)

     # 4. Create assets_current Table
    table_id = f"{dataset_ref}.assets_current"
    schema_assets = [
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("ip", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("vendor", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("last_seen", "STRING", mode="NULLABLE"),
    ]
    create_table_if_not_exists(client, table_id, schema_assets)

    # 5. Create raw_erp_orders Table
    table_id = f"{dataset_ref}.raw_erp_orders"
    schema_erp = [
        bigquery.SchemaField("order_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("due_date", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "STRING", mode="REQUIRED"),
    ]
    create_table_if_not_exists(client, table_id, schema_erp)


def create_table_if_not_exists(client, table_id, schema):
    try:
        client.get_table(table_id)
        print(f"Table {table_id} already exists.")
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)
        print(f"Created table {table_id}.")

if __name__ == "__main__":
    init_bq()
