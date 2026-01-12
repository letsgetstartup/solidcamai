import json
import os
import logging
from typing import Optional, Dict, Any
from simco_agent.config import settings

logger = logging.getLogger("simco_agent.device_state")

class DeviceState:
    """Handles persistence of device identity and binding."""

    def __init__(self, state_file: Optional[str] = None):
        self.state_file = state_file or settings.DEVICE_STATE_FILE
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load device state: {e}")
                self.data = {}
        else:
            self.data = {}

    def save(self):
        try:
            # Atomic write
            tmp_file = f"{self.state_file}.tmp"
            with open(tmp_file, "w") as f:
                json.dump(self.data, f, indent=2)
            os.rename(tmp_file, self.state_file)
        except Exception as e:
            logger.error(f"Failed to save device state: {e}")

    @property
    def device_id(self) -> Optional[str]:
        return self.data.get("device_id")

    @property
    def is_enrolled(self) -> bool:
        return bool(self.device_id)

    def update(self, **kwargs):
        self.data.update(kwargs)
        self.save()
