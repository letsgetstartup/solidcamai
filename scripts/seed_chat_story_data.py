import time
import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from google.cloud import bigquery

# --- Configuration ---
PROJECT_ID = "solidcamal"
DATASET_ID = "simco_telemetry"
TENANT_ID = "tenant_demo"
SITE_ID = "test_site"

def seed_story_data():
    client = bigquery.Client(project=PROJECT_ID)
    now = datetime.now(timezone.utc)
    
    # --- Machines matching the story ---
    # VMC-1, VMC-2, VMC-3, Lathe-1, Lathe-2 are explicitly mentioned
    machines = [
        {"id": "VMC-1", "type": "MILL"},
        {"id": "VMC-2", "type": "MILL"},
        {"id": "VMC-3", "type": "MILL"},
        {"id": "Lathe-1", "type": "LATHE"},
        {"id": "Lathe-2", "type": "LATHE"},
        {"id": "Okuma-Gen-4", "type": "MILL"},
        {"id": "Doosan-DN-7", "type": "LATHE"},
    ]

    print("1. Clearing existing testing data for story consistency (optional, but cleaner)...")
    # For now, we just append. The query limits to recent data anyway.

    # --- 2. Seed ERP Orders (The 'Profitability' Story) ---
    print("2. Seeding ERP Orders...")
    erp_table = f"{PROJECT_ID}.{DATASET_ID}.raw_erp_orders"
    erp_rows = []
    
    # Specific Order #ORD-101 (Active)
    erp_rows.append({
        "tenant_id": TENANT_ID,
        "site_id": SITE_ID,  "source_system": "SAP", "connection_id": "conn1", "entity": "orders",
        "source_pk": "ORD-101", "ingest_ts": now.isoformat(), "source_updated_at": now.isoformat(),
        "order_id": "ORD-101", "product_id": "SHAFT-X1", "status": "IN_PROGRESS", "quantity": 500,
        "due_date": (now + timedelta(days=2)).date().isoformat(), # Due soon
        "payload": json.dumps({"description": "High precision shaft for client X"})
    })

    # Orders created 'Today'
    for i in range(5):
        oid = f"ORD-NEW-{i}"
        erp_rows.append({
            "tenant_id": TENANT_ID, "site_id": SITE_ID, "source_system": "SAP", "connection_id": "conn1", "entity": "orders",
            "source_pk": oid, "ingest_ts": now.isoformat(), "source_updated_at": now.isoformat(),
            "order_id": oid, "product_id": f"PART-{i}", "status": "RELEASED", "quantity": 100 + i*10,
            "due_date": (now + timedelta(days=5)).date().isoformat(),
            "payload": json.dumps({})
        })

    # Orders due tomorrow ("Deadline Risk")
    for i in range(3):
        oid = f"ORD-URGENT-{i}"
        erp_rows.append({
            "tenant_id": TENANT_ID, "site_id": SITE_ID, "source_system": "SAP", "connection_id": "conn1", "entity": "orders",
            "source_pk": oid, "ingest_ts": now.isoformat(), "source_updated_at": now.isoformat(),
            "order_id": oid, "product_id": f"FAST-PART-{i}", "status": "IN_PROGRESS", "quantity": 50,
            "due_date": (now + timedelta(days=1)).date().isoformat(),
            "payload": json.dumps({})
        })
        
    client.insert_rows_json(erp_table, erp_rows)

    # --- 3. Seed Telemetry (The 'Health' & 'Energy' Story) ---
    print("3. Seeding Telemetry...")
    telemetry_table = f"{PROJECT_ID}.{DATASET_ID}.raw_telemetry"
    tel_rows = []
    
    # Generate 1 hour of data at 1-min resolution
    for i in range(60): 
        ts = now - timedelta(minutes=i)
        
        # VMC-3: High Spindle Load ("Spindle Overheat")
        tel_rows.append({
            "record_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
            "machine_id": "VMC-3", "timestamp": ts.isoformat(), "status": "RUNNING",
            "metrics": json.dumps({"spindle_load": random.uniform(85, 95), "power_kw": 15.5, "vibration": 0.2}) # >80%
        })
        
        # Lathe-1: Vibration Spike
        tel_rows.append({
            "record_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
            "machine_id": "Lathe-1", "timestamp": ts.isoformat(), "status": "RUNNING",
            "metrics": json.dumps({"spindle_load": 40, "power_kw": 8.0, "vibration": random.uniform(2.5, 4.0)}) # High vibe
        })

        # VMC-1: High Power ("Energy Hog")
        tel_rows.append({
            "record_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
            "machine_id": "VMC-1", "timestamp": ts.isoformat(), "status": "RUNNING",
            "metrics": json.dumps({"spindle_load": 60, "power_kw": random.uniform(25, 30), "vibration": 0.5}) # High power
        })
        
        # Others normal
        for m in ["VMC-2", "Lathe-2", "Okuma-Gen-4"]:
            tel_rows.append({
                "record_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
                "machine_id": m, "timestamp": ts.isoformat(), "status": "ACTIVE",
                "metrics": json.dumps({"spindle_load": random.uniform(20, 50), "power_kw": random.uniform(5, 12), "vibration": 0.1})
            })
            
    client.insert_rows_json(telemetry_table, tel_rows)

    # --- 4. Seed Events (The 'Efficiency', 'Tools', 'Workforce', 'Quality' Story) ---
    print("4. Seeding Events...")
    events_table = f"{PROJECT_ID}.{DATASET_ID}.raw_events"
    evt_rows = []
    
    # VMC-1: DOWNTIME today
    for i in range(3):
        ts = now - timedelta(hours=random.randint(1, 10))
        evt_rows.append({
            "event_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
            "machine_id": "VMC-1", "timestamp": ts.isoformat(), "type": "DOWNTIME", "severity": "CRITICAL",
            "details": json.dumps({"reason": "Motor failure"})
        })

    # VMC-2: TOOL_CHANGE
    ts = now - timedelta(minutes=15)
    evt_rows.append({
        "event_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
        "machine_id": "VMC-2", "timestamp": ts.isoformat(), "type": "TOOL_CHANGE", "severity": "LOW",
        "details": json.dumps({"tool_id": "T4", "life_remaining": 10})
    })

    # Workforce: OPERATOR_LOGIN
    operators = ["Alice", "Bob", "Charlie"]
    for op in operators:
        ts = now - timedelta(hours=random.randint(1, 8))
        evt_rows.append({
            "event_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
            "machine_id": "General", "timestamp": ts.isoformat(), "type": "OPERATOR_LOGIN", "severity": "INFO",
            "details": json.dumps({"operator": op})
        })

    # Quality: PART_COMPLETE and QC_CHECK
    for m in machines:
        mid = m["id"]
        # Parts
        for i in range(5):
            ts = now - timedelta(minutes=random.randint(10, 300))
            evt_rows.append({
                "event_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
                "machine_id": mid, "timestamp": ts.isoformat(), "type": "PART_COMPLETE", "severity": "INFO",
                "details": json.dumps({"part_id": f"P-{random.randint(100,999)}"})
            })
        # QC Checks
        ts = now - timedelta(minutes=random.randint(10, 60))
        evt_rows.append({
            "event_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
            "machine_id": mid, "timestamp": ts.isoformat(), "type": "QC_CHECK", "severity": "INFO",
            "details": json.dumps({"passed": True})
        })

    # "Machines with most ALARMS": Generate alarms for VMC-1, VMC-3, Lathe-1
    for m in ["VMC-1", "VMC-3", "Lathe-1", "Doosan-DN-7", "Okuma-Gen-4"]:
        count = random.randint(3, 8)
        for i in range(count):
             ts = now - timedelta(minutes=random.randint(10, 600))
             evt_rows.append({
                "event_id": str(uuid.uuid4()), "tenant_id": TENANT_ID, "site_id": SITE_ID,
                "machine_id": m, "timestamp": ts.isoformat(), "type": "ALARM", "severity": "HIGH",
                "details": json.dumps({"code": "ERR-505"})
            })

    client.insert_rows_json(events_table, evt_rows)
    print("Story data seeded successfully!")

if __name__ == "__main__":
    seed_story_data()
