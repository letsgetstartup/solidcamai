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
    
    # PR3: Using Pairing Code instead of legacy bootstrap
    pairing_code = settings.PAIRING_CODE
    if not pairing_code:
        logger.warning("No PAIRING_CODE configured. Enrollment paused.")
        return

    payload = {
        "pairing_code": pairing_code, # PR3
        "hardware_info": {
            "hostname": os.uname().nodename,
            "mac": "00:00:00:00:00:00", # Mocked
            "runtime_version": settings.VERSION
        }
    }

    try:
        response = requests.post(enroll_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        state.update(
            device_id=data["device_id"],
            gateway_token=data.get("gateway_token"), # PR4: Persist Token
            tenant_id=data["tenant_id"],
            site_id=data["site_id"],
            channel=data.get("channel", "prod"),
            config_version=data.get("config_version", 1),
            enrolled_at=time.time()
        )
        logger.info(f"Enrollment successful! Device ID: {state.device_id}")
    except Exception as e:
        logger.error(f"Enrollment failed: {e}")
        raise
