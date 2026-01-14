import time
import json
import logging
import random
import requests
from datetime import datetime
import uuid

# --- Configuration ---
INGEST_URL = "https://ingest-erp-i6yvrrps6q-uc.a.run.app"
TENANT_ID = "tenant_demo"
SITE_ID = "site_demo"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIMCO_ERP_AGENT")

class ERPSimulationAgent:
    def __init__(self):
        self.products = ["Part-A-100", "Part-B-200", "Assy-X-99", "Flange-Z-10"]
        self.statuses = ["RELEASED", "IN_PROGRESS", "COMPLETED", "HOLD"]

    def generate_orders(self, count=2):
        orders = []
        for _ in range(count):
            order_id = f"WO-{random.randint(1000, 9999)}"
            order = {
                "order_id": order_id,
                "tenant_id": TENANT_ID,
                "site_id": SITE_ID,
                "product_id": random.choice(self.products),
                "quantity": random.randint(10, 500),
                "due_date": datetime.utcnow().isoformat(),
                "status": random.choice(self.statuses),
            }
            orders.append(order)
        return orders

    def push_to_cloud(self, orders):
        try:
            payload = {"orders": orders}
            response = requests.post(INGEST_URL, json=payload, timeout=10)
            if response.status_code in [200, 201]:
                logger.info(f"Successfully pushed {len(orders)} orders. Status: {response.status_code}")
                logger.debug(f"Response: {response.text}")
            else:
                logger.error(f"Failed to push. Status: {response.status_code} Body: {response.text}")
        except Exception as e:
            logger.error(f"Network error: {e}")

if __name__ == "__main__":
    agent = ERPSimulationAgent()
    logger.info("Starting ERP Simulation Agent...")
    logger.info(f"Target URL: {INGEST_URL}")
    
    try:
        while True:
            data = agent.generate_orders(count=random.randint(1, 3))
            agent.push_to_cloud(data)
            time.sleep(10) # Less frequent than telemetry
    except KeyboardInterrupt:
        logger.info("Stopping...")
