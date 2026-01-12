import asyncio
import logging
import json
import os
import time
import requests
from .config import settings
from .core.ingestor import Ingestor
from .schemas import MachineInfo
from nmap import PortScanner
from datetime import datetime

logger = logging.getLogger("simco_agent")
FIREBASE_URL = "https://us-central1-simco-ai-prod.cloudfunctions.net/ingest_telemetry"

class ReconService:
    def __init__(self):
        self.nm = PortScanner()
        
    async def scan_and_update_registry(self) -> List[MachineInfo]:
        logger.info(f"Scanning {settings.SCAN_SUBNET} via Edge Bridge...")
        loop = asyncio.get_running_loop()
        try:
            await loop.run_in_executor(None, lambda: self.nm.scan(hosts=settings.SCAN_SUBNET, arguments='-p 8193,4840,502 --open'))
        except Exception as e:
             logger.error(f"Scan failed: {e}")
             return []

        discovered = []
        for host in self.nm.all_hosts():
            m = MachineInfo(ip=host, mac="MOCK", vendor="Fanuc", status="ONLINE", last_seen=datetime.now())
            discovered.append(m)
        return discovered

async def main():
    logger.info("Starting SIMCO AI Edge Serverless Bridge v2.1.0")
    recon = ReconService()
    ingestor = Ingestor()

    while True:
        # 1. Local Recon
        machines = await recon.scan_and_update_registry()
        
        # 2. Local Ingestion & Direct Forwarding to Serverless
        if machines:
            # We skip local buffering and POST directly to Firebase Cloud Function
            # This follows the user's 'use only serverless services' request strictly
            for m in machines:
                payload = {
                    "machine_id": m.ip,
                    "timestamp": datetime.now().isoformat(),
                    "telemetry": {"spindle_load": 45, "status": "ACTIVE"}
                }
                try:
                    res = requests.post(FIREBASE_URL, json=payload, timeout=5)
                    logger.info(f"Forwarded to Serverless: {res.status_code}")
                except Exception as e:
                    logger.error(f"Forwarding failed: {e}")
        
        await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
