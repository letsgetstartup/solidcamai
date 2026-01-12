from typing import Optional
from .base import BaseDriver
from .fanuc import FanucDriver

class DriverFactory:
    @staticmethod
    def get_driver(vendor: str, ip: str) -> Optional[BaseDriver]:
        vendor = vendor.lower()
        if "fanuc" in vendor:
            return FanucDriver(ip)
        # Placeholder for other drivers (OPC-UA, Haas, etc)
        # if "opc" in vendor: return OpcUaDriver(ip)
        
        return None
