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


async def main():
    logger.info("Starting SIMCO AI Edge Serverless Bridge v2.3.0")
    
    # 1. Fleet Provisioning
    from .core.device_state import DeviceState
    from .core.provisioning import ensure_enrolled
    state = DeviceState()
    try:
        ensure_enrolled(state)
    except Exception:
        logger.critical("Failed to enroll device. Shuting down for safety.")
        return

    # 2. Start Management Services
    from .core.config_manager import ConfigManager
    from .core.heartbeat import HeartbeatAgent
    from .core.uplink_worker import UplinkWorker
    
    config_mgr = ConfigManager(state)
    heartbeat = HeartbeatAgent(state)
    uplink = UplinkWorker()
    
    # Launch background tasks
    tasks = [
        asyncio.create_task(config_mgr.run()),
        asyncio.create_task(heartbeat.run()),
        asyncio.create_task(uplink.run())
    ]

    from .discovery.orchestrator import DiscoveryOrchestrator
    orchestrator = DiscoveryOrchestrator()
    ingestor = Ingestor(state)

    try:
        while True:
            # 3. Local Discovery (Policy-Driven)
            logger.info("Executing periodic discovery cycle...")
            # We wrap in executor if it performs blocking nmap scans
            loop = asyncio.get_running_loop()
            candidates = await loop.run_in_executor(None, orchestrator.run_discovery_cycle)
            
            # 4. Ingestion Cycle (Drivers)
            from .core.registry import load_registry
            registry = load_registry()
            if registry:
                await ingestor.ingest_cycle(registry)
            
            await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)
    finally:
        config_mgr.stop()
        heartbeat.stop()
        uplink.stop()
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
