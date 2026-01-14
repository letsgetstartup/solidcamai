import time
import json
import logging
import random
import requests
from datetime import datetime

# --- Configuration ---
INGEST_URL = "https://ingest-telemetry-i6yvrrps6q-uc.a.run.app"
ASSETS_URL = "https://ingest-assets-i6yvrrps6q-uc.a.run.app"
TENANT_ID = "tenant_demo"
SITE_ID = "site_demo"
DEVICE_ID = "sim_device_01"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIMCO_AI_AGENT")

class SimulationAgent:
    def __init__(self):
        self.machines = [
            {"id": "fanuc_cnc_01", "ip": "192.168.1.101", "vendor": "Fanuc"},
            {"id": "haas_vmc_02", "ip": "192.168.1.102", "vendor": "Haas"},
            {"id": "siemens_840d_03", "ip": "192.168.1.103", "vendor": "Siemens"}
        ]
        self.register_assets()

    def register_assets(self):
        logger.info("Registering assets...")
        for m in self.machines:
            payload = {
                "machine_id": m["id"],
                "tenant_id": TENANT_ID,
                "site_id": SITE_ID,
                "ip": m["ip"],
                "vendor": m["vendor"],
                "last_seen": datetime.utcnow().isoformat()
            }
            try:
                response = requests.post(ASSETS_URL, json=payload, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Registered {m['id']}")
                else:
                    logger.warning(f"Failed to register {m['id']}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error registering {m['id']}: {e}")

    def generate_telemetry(self):
        records = []
        for m in self.machines:
            # Simulate realistic data
            status = random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "IDLE", "RUNNING"])
            spindle = random.uniform(0, 100) if status != "IDLE" else 0
            
            record = {
                "record_id": f"{m['id']}_{int(time.time()*1000)}",
                "machine_id": m["id"],
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "metrics": {
                    "spindle_load": spindle,
                    "feed_rate": random.uniform(0, 5000) if status == "RUNNING" else 0,
                    "temperature": random.uniform(30, 65)
                },
                "ip": m["ip"],
                "vendor": m["vendor"],
                "tenant_id": TENANT_ID,
                "site_id": SITE_ID
            }
            records.append(record)
        return records

    def push_to_cloud(self, records):
        try:
            payload = {
                "records": records,
                "device_id": DEVICE_ID
            }
            # Add valid v3 headers if needed, but the basic ingest might not enforce strict Auth yet
            # based on my review of main.py, ingest_telemetry just checks POST and JSON.
            # But let's verify if main.py enforces auth.
            # main.py: ingest_telemetry does NOT have @cors_enabled or explicit auth check in the snippet I saw.
            # It just does validation.
            
            response = requests.post(INGEST_URL, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"Successfully pushed {len(records)} records. Status: {response.status_code}")
                logger.info(f"Response: {response.text}")
            else:
                logger.error(f"Failed to push. Status: {response.status_code} Body: {response.text}")
        except Exception as e:
            logger.error(f"Network error: {e}")

if __name__ == "__main__":
    agent = SimulationAgent()
    logger.info("Starting Simulation Agent...")
    logger.info(f"Target URL: {INGEST_URL}")
    
    try:
        while True:
            data = agent.generate_telemetry()
            agent.push_to_cloud(data)
            time.sleep(5) 
    except KeyboardInterrupt:
        logger.info("Stopping...")
