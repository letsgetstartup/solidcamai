import asyncio
import logging
import requests
import json
import os
from datetime import datetime
from typing import Optional
from simco_agent.config import settings
from simco_agent.core.device_state import DeviceState
from simco_agent.core.buffer_manager import BufferManager
from simco_agent.discovery.orchestrator import DiscoveryOrchestrator
from simco_agent.core.registry import load_registry, save_registry

logger = logging.getLogger("simco_agent.config_manager")

class ConfigManager:
    """Polls for configuration updates and applies them to the agent."""

    def __init__(self, state: Optional[DeviceState] = None):
        self.state = state or DeviceState()
        self.poll_interval = settings.CONFIG_POLL_INTERVAL_SECONDS
        self.running = False

    async def run(self):
        self.running = True
        logger.info("ConfigManager started.")
        
        while self.running:
            try:
                if not self.state.is_enrolled:
                    await asyncio.sleep(10)
                    continue

                await self._poll_config()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Config poll failed: {e}")
                await asyncio.sleep(30)

    async def _poll_config(self):
        url = f"{settings.MGMT_BASE_URL}/get_config"
        payload = {
            "device_id": self.state.device_id,
            "current_config_version": self.state.data.get("config_version", 0)
        }
        
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, timeout=10))
            if response.status_code == 200:
                data = response.json()
                if data.get("changed"):
                    logger.info(f"Config update received: v{data['config_version']}")
                    self._apply_config(data["config"], data["config_version"])
            else:
                logger.debug(f"No config change (Status: {response.status_code})")
        except Exception as e:
            logger.error(f"Config request failed: {e}")

    def _apply_config(self, new_config: dict, version: int):
        # 1. Update Persistent State
        self.state.update(config_version=version, last_config_update=version)
        
        # 2. Handle Discovery Policy Updates
        orch = DiscoveryOrchestrator() # In production, use a shared instance
        orch.update_policy(new_config)

        # 3. Handle Manual Enrollments
        manual_entries = new_config.get("pending_manual_enrollments", [])
        if manual_entries:
            registry = load_registry()
            existing_ips = {m.get("ip") for m in registry}
            
            applied_count = 0
            for entry in manual_entries:
                ip = entry.get("machine_ip")
                if ip and ip not in existing_ips:
                    registry.append({
                        "machine_id": entry.get("machine_id", ip),
                        "ip": ip,
                        "status": "MANUAL_ENROLLED",
                        "source": "manual_portal",
                        "last_seen": datetime.utcnow().isoformat(),
                        "vendor": entry.get("vendor", "UNKNOWN"),
                        "preferred_driver": entry.get("preferred_driver_id")
                    })
                    applied_count += 1
            
            if applied_count > 0:
                save_registry(registry)
                logger.info(f"Manual Enrollment: Applied {applied_count} new machines from cloud config.")

        # 4. Emit CONFIG_CHANGED event
        event = {
            "machine_id": "EDGE_GATEWAY",
            "timestamp": datetime.utcnow().isoformat(),
            "type": "CONFIG_CHANGED",
            "severity": "INFO",
            "details": {"new_version": version, "config_keys": list(new_config.keys())}
        }
        logger.info(f"Applied remote configuration v{version}")

    def stop(self):
        self.running = False
