import os
import json
import importlib.util
from typing import Optional, Dict, Any
from .base import BaseDriver
from .fanuc import FanucDriver
from .generic import GenericProtocolDriver
from simco_agent.config import settings

class DriverFactory:
    @staticmethod
    def get_driver(vendor: str, ip: str, driver_id: Optional[str] = None) -> BaseDriver:
        vendor_normalized = vendor.lower()
        
        # 1. Try to resolve driver_id if not provided
        if not driver_id:
            # Simple heuristic or vendor-based resolution could go here
            if "fanuc" in vendor_normalized:
                driver_id = "fanuc"

        # 2. Try Dynamic Load from Active Drivers
        if driver_id:
            active_dir = os.path.join(settings.DRIVERS_ACTIVE_DIR, driver_id, "current")
            if os.path.exists(active_dir):
                try:
                    meta_path = os.path.join(active_dir, "metadata.json")
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                    
                    entrypoint = meta.get("entrypoint", "driver:Driver")
                    module_name, class_name = entrypoint.split(":")
                    
                    module_path = os.path.join(active_dir, f"{module_name}.py")
                    if os.path.exists(module_path):
                        spec = importlib.util.spec_from_file_location(f"dynamic_driver.{driver_id}", module_path)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        driver_class = getattr(module, class_name)
                        print(f"Loaded dynamic driver: {driver_id} ({version if (version := meta.get('version')) else 'unknown'})")
                        return driver_class(ip)
                except Exception as e:
                    print(f"Failed to load dynamic driver {driver_id}: {e}")

        # 3. Fallback to Built-in Drivers
        if "fanuc" in vendor_normalized:
            return FanucDriver(ip)
        
        # 4. Ultimate Fallback (Directive Requirement: Always return a driver)
        print(f"Using GenericProtocolDriver for {vendor} ({ip})")
        return GenericProtocolDriver(ip)
