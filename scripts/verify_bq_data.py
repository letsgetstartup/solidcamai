from google.cloud import bigquery
import json
import time

def verify_bq_data():
    client = bigquery.Client(project="solidcamal")
    table_id = "solidcamal.simco_telemetry.raw_telemetry"
    
    print("Waiting for data ingestion (10s)...")
    time.sleep(10)

    print(f"\nQuerying {table_id} for latest 10 records...")
    
    query = f"""
        SELECT machine_id, timestamp, status, metrics
        FROM `{table_id}` 
        ORDER BY timestamp DESC
        LIMIT 10
    """
    
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        
        if results:
            print(f"Found {len(results)} Telemetry records:")
            for row in results:
                # Format nicely
                metrics_str = row.metrics
                if isinstance(metrics_str, str): # If we stored as string
                     try:
                         metrics_str = json.loads(metrics_str)
                     except: pass
                
                print(f"[{row.timestamp}] {row.machine_id} | Status: {row.status} | Metrics: {metrics_str}")
        else:
            print("No Telemetry records found.")

    except Exception as e:
        print(f"Error querying Telemetry: {e}")

    # --- Verify ERP Data ---
    erp_table_id = "solidcamal.simco_telemetry.raw_erp_orders"
    print(f"\nQuerying {erp_table_id} for latest 5 orders...")
    
    erp_query = f"""
        SELECT order_id, product_id, quantity, status, timestamp
        FROM `{erp_table_id}`
        ORDER BY timestamp DESC
        LIMIT 5
    """

    try:
        erp_job = client.query(erp_query)
        erp_results = list(erp_job.result())

        if erp_results:
             print(f"Found {len(erp_results)} ERP Orders:")
             for row in erp_results:
                 print(f"[{row.timestamp}] Order: {row.order_id} | Product: {row.product_id} | Qty: {row.quantity} | Status: {row.status}")
        else:
             print("No ERP orders found.")
             
    except Exception as e:
        print(f"Error querying ERP: {e}")

if __name__ == "__main__":
    verify_bq_data()
