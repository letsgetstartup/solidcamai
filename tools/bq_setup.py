from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bq_setup")

PROJECT_ID = "solidcam-ai-platform" # Replace/Env Not Set
DATASET_ID = "simco_telemetry" # Multi-tenant dataset

def setup_bigquery():
    client = bigquery.Client()
    
    # 1. Dataset
    dataset_ref = client.dataset(DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
        logger.info(f"Dataset {DATASET_ID} exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US" # or EU
        client.create_dataset(dataset)
        logger.info(f"Created dataset {DATASET_ID}.")
        
    # 2. Raw Telemetry Table
    # Partitioned by timestamp (Day), Clustered by tenant/site/machine
    telemetry_ref = dataset_ref.table("raw_telemetry")
    schema = [
        bigquery.SchemaField("record_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("device_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("metrics", "JSON", mode="NULLABLE"), # JSON type is best for flexible metrics
        bigquery.SchemaField("driver", "JSON", mode="NULLABLE")
    ]
    
    try:
        client.get_table(telemetry_ref)
        logger.info("Table raw_telemetry exists.")
    except NotFound:
        table = bigquery.Table(telemetry_ref, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        table.clustering_fields = ["tenant_id", "site_id", "machine_id"]
        client.create_table(table)
        logger.info("Created table raw_telemetry.")

    # 3. Raw Events Table
    events_ref = dataset_ref.table("raw_events")
    events_schema = [
        bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("device_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("actor_user_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("severity", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("details", "JSON", mode="NULLABLE")
    ]
    
    try:
        client.get_table(events_ref)
        logger.info("Table raw_events exists.")
    except NotFound:
        table = bigquery.Table(events_ref, schema=events_schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        table.clustering_fields = ["tenant_id", "site_id", "machine_id"]
        client.create_table(table)
        logger.info("Created table raw_events.")

    # 4. authorized_users (for RLS/Lookup) - Target Requirement
    users_ref = dataset_ref.table("authorized_users")
    users_schema = [
        bigquery.SchemaField("user_email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("role", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE")
    ]
    try:
        client.get_table(users_ref)
    except NotFound:
        table = bigquery.Table(users_ref, schema=users_schema)
        client.create_table(table)
        logger.info("Created table authorized_users.")

    # 5. Output RLS Policy DDL (Agent D Requirement)
    print("\n--- RLS Policy DDL (Manual Apply) ---")
    print(f"""
    CREATE ROW ACCESS POLICY tenant_isolation_policy
    ON `{DATASET_ID}.raw_telemetry`
    GRANT TO ('user:all_authenticated_users')
    FILTER USING (
      tenant_id IN (
        SELECT tenant_id 
        FROM `{DATASET_ID}.authorized_users`
        WHERE user_email = SESSION_USER()
      )
    );
    """)
    print("-------------------------------------\n")

    # 6. ERP Raw Table
    erp_raw_ref = dataset_ref.table("erp_raw")
    erp_raw_schema = [
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_system", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("connection_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entity", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_pk", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("source_updated_at", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("ingest_ts", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("payload", "JSON", mode="NULLABLE")
    ]
    try:
        client.get_table(erp_raw_ref)
        logger.info("Table erp_raw exists.")
    except NotFound:
        table = bigquery.Table(erp_raw_ref, schema=erp_raw_schema)
        table.time_partitioning = bigquery.TimePartitioning(type_=bigquery.TimePartitioningType.DAY, field="ingest_ts")
        table.clustering_fields = ["tenant_id", "source_system", "entity", "source_pk"]
        client.create_table(table)
        logger.info("Created table erp_raw.")

    # 7. ERP Machine Map Table
    map_ref = dataset_ref.table("erp_machine_map")
    map_schema = [
        bigquery.SchemaField("tenant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("machine_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("erp_system", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("erp_resource_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("valid_from", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("valid_to", "TIMESTAMP", mode="NULLABLE"),
        bigquery.SchemaField("created_by_user_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    try:
        client.get_table(map_ref)
        logger.info("Table erp_machine_map exists.")
    except NotFound:
        table = bigquery.Table(map_ref, schema=map_schema)
        table.clustering_fields = ["tenant_id", "site_id", "machine_id"]
        client.create_table(table)
        logger.info("Created table erp_machine_map.")

if __name__ == "__main__":
    setup_bigquery()
