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
SITE_ID = "site_demo"

def seed_data():
    client = bigquery.Client(project=PROJECT_ID)
    now = datetime.now(timezone.utc)
    
    machines = [
        {"id": "fanuc_cnc_01", "ip": "192.168.1.101", "vendor": "Fanuc", "res": "RES-001"},
        {"id": "haas_vmc_02", "ip": "192.168.1.102", "vendor": "Haas", "res": "RES-002"},
        {"id": "siemens_840d_03", "ip": "192.168.1.103", "vendor": "Siemens", "res": "RES-003"},
        {"id": "okuma_gen_04", "ip": "192.168.1.104", "vendor": "Okuma", "res": "RES-004"},
        {"id": "dmg_mori_05", "ip": "192.168.1.105", "vendor": "DMG Mori", "res": "RES-005"},
        {"id": "mazak_int_06", "ip": "192.168.1.106", "vendor": "Mazak", "res": "RES-006"},
        {"id": "doosan_dn_07", "ip": "192.168.1.107", "vendor": "Doosan", "res": "RES-007"},
        {"id": "makino_a51_08", "ip": "192.168.1.108", "vendor": "Makino", "res": "RES-008"},
        {"id": "bro_speed_09", "ip": "192.168.1.109", "vendor": "Brother", "res": "RES-009"}
    ]

    # 1. Seed assets_current
    print("Seeding assets_current...")
    assets_table = f"{PROJECT_ID}.{DATASET_ID}.assets_current"
    asset_rows = []
    for m in machines:
        asset_rows.append({
            "machine_id": m["id"],
            "tenant_id": TENANT_ID,
            "site_id": SITE_ID,
            "ip": m["ip"],
            "vendor": m["vendor"],
            "last_seen": now.isoformat()
        })
    client.insert_rows_json(assets_table, asset_rows)

    # 2. Seed erp_machine_map
    print("Seeding erp_machine_map...")
    map_table = f"{PROJECT_ID}.{DATASET_ID}.erp_machine_map"
    map_rows = []
    for m in machines:
        map_rows.append({
            "tenant_id": TENANT_ID,
            "site_id": SITE_ID,
            "machine_id": m["id"],
            "erp_system": "SAP_B1",
            "erp_resource_code": m["res"],
            "created_at": now.isoformat()
        })
    client.insert_rows_json(map_table, map_rows)

    # 3. Seed erp_raw (Production Orders)
    print("Seeding erp_raw...")
    erp_raw_table = f"{PROJECT_ID}.{DATASET_ID}.erp_raw"
    erp_rows = []
    products = ["FAN-SHAFT-01", "HAAS-BRACKET-X", "SIE-GEAR-MOD3"]
    operators = ["Avi M.", "John D.", "Sarah L.", "Mike R.", "Elena S."]
    for i in range(15):
        m = random.choice(machines)
        order_id = 1000 + i
        ts = now - timedelta(days=random.randint(0, 3))
        payload = {
            "DocEntry": str(order_id),
            "ProductionOrder": f"WO-{order_id}",
            "ItemNo": random.choice(products),
            "Status": random.choice(["RELEASED", "IN_PROGRESS", "RELEASED"]),
            "DueDate": (now + timedelta(days=random.randint(-2, 10))).isoformat(),
            "UpdateDate": ts.date().isoformat(),
            "ResourceCode": m["res"],
            "OperatorName": random.choice(operators)
        }
        erp_rows.append({
            "tenant_id": TENANT_ID,
            "source_system": "SAP_B1",
            "connection_id": "conn_01",
            "entity": "production_orders",
            "source_pk": str(order_id),
            "source_updated_at": ts.isoformat(),
            "ingest_ts": now.isoformat(),
            "payload": json.dumps(payload)
        })
    client.insert_rows_json(erp_raw_table, erp_rows)

    # 4. Seed raw_telemetry (Last 3 hours, every 1 minute)
    print("Seeding raw_telemetry...")
    telemetry_table = f"{PROJECT_ID}.{DATASET_ID}.raw_telemetry"
    tel_rows = []
    for m in machines:
        for i in range(180): # 3 hours
            ts = now - timedelta(minutes=i)
            status = random.choice(["ACTIVE", "RUNNING", "IDLE"])
            tel_rows.append({
                "record_id": f"sim_{m['id']}_{int(ts.timestamp())}",
                "tenant_id": TENANT_ID,
                "site_id": SITE_ID,
                "machine_id": m["id"],
                "timestamp": ts.isoformat(),
                "status": status,
                "metrics": json.dumps({
                    "spindle_load": random.uniform(10, 90) if status != "IDLE" else 0,
                    "feed_rate": random.uniform(100, 2000) if status == "RUNNING" else 0,
                    "power_kw": random.uniform(5, 25)
                })
            })
            if len(tel_rows) >= 500:
                client.insert_rows_json(telemetry_table, tel_rows)
                tel_rows = []
    if tel_rows: client.insert_rows_json(telemetry_table, tel_rows)

    # 5. Seed raw_events
    print("Seeding raw_events...")
    events_table = f"{PROJECT_ID}.{DATASET_ID}.raw_events"
    evt_rows = []
    for m in machines:
        for i in range(5):
            ts = now - timedelta(hours=random.randint(1, 48))
            evt_type = random.choice(["ALARM", "DOWNTIME"])
            evt_rows.append({
                "event_id": str(uuid.uuid4()),
                "tenant_id": TENANT_ID,
                "site_id": SITE_ID,
                "machine_id": m["id"],
                "timestamp": ts.isoformat(),
                "type": evt_type,
                "severity": random.choice(["MEDIUM", "HIGH", "CRITICAL"]),
                "details": json.dumps({
                    "message": f"Simulated {evt_type} for {m['id']}",
                    "duration_seconds": random.randint(60, 3600)
                })
            })
    client.insert_rows_json(events_table, evt_rows)

    print("Data seeding completed successfully.")

if __name__ == "__main__":
    seed_data()
