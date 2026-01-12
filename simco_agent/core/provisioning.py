import requests
import logging
import os
from typing import Dict, Any
from simco_agent.config import settings
from simco_agent.core.device_state import DeviceState

logger = logging.getLogger("simco_agent.provisioning")

def ensure_enrolled(state: DeviceState = None):
    """Ensures the device is enrolled and has a valid identity."""
    state = state or DeviceState()
    
    if state.is_enrolled:
        logger.info(f"Device already enrolled: {state.device_id}")
        return

    logger.info("Starting device enrollment...")
    enroll_url = f"{settings.MGMT_BASE_URL}/enroll"
    
    payload = {
        "bootstrap_token": settings.BOOTSTRAP_TOKEN,
        "device_fingerprint": {
            "hostname": os.uname().nodename,
            "mac": "00:00:00:00:00:00", # Mocked for now
            "runtime_version": "2.2.0"
        },
        "requested_channel": "dev"
    }

    try:
        response = requests.post(enroll_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        state.update(
            device_id=data["device_id"],
            tenant_id=data["tenant_id"],
            site_id=data["site_id"],
            channel=data["channel"],
            config_version=data["config_version"],
            enrolled_at=os.times().elapsed
        )
        logger.info(f"Enrollment successful! Device ID: {state.device_id}")
    except Exception as e:
        logger.error(f"Enrollment failed: {e}")
        raise
