import logging
import asyncio
import requests
import xml.etree.ElementTree as ET
from typing import Optional
from simco_agent.drivers.common.models import Fingerprint
from . import ProbeInterface

logger = logging.getLogger(__name__)

class MTConnectProbe(ProbeInterface):
    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        with open("/tmp/mtconnect_debug.txt", "a") as f:
            f.write(f"Starting run {ip}:{port}\n")
            
        url = f"http://{ip}:{port}/current"
        loop = asyncio.get_event_loop()
        
        try:
            # Run blocking I/O in executor
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, timeout=2)
            )
            
            if response.status_code != 200:
                with open("/tmp/mtconnect_debug.txt", "a") as f:
                    f.write(f"DEBUG: Status Code {response.status_code}\n")
                return None
                
            # Basic XML Parse
            # Namespace handling can be tricky in ElementTree, stripping namespaces for simplicity
            xml_content = response.text
            # Remove namespaces for easier find operations (naive but effective for probing)
            # Alternatively use check for 'MTConnectStreams' tag
            
            if "MTConnectStreams" not in xml_content:
                with open("/tmp/mtconnect_debug.txt", "a") as f:
                    f.write(f"DEBUG: MTConnectStreams tag not found in {xml_content[:100]}\n")
                return None
                
            try:
                root = ET.fromstring(xml_content)
                header = root.find(".//Header") # Use xpath to find header anywhere or adjust if namespace striped
                
                # If namespace exists, find might fail without map.
                # Let's try simple string scraping for robustness if XML parse is fragile without complete schema
                # But let's try to be decent.
                
                # Header attributes often have 'sender', 'version'
                # If root has namespace: {urn:mtconnect.org:MTConnectStreams:1.3}Header
                pass
            except ET.ParseError:
                logger.debug(f"MTConnect XML parse error for {ip}:{port}")
                return None

            # String based extraction is often more robust for simple banner grabbing than strict XML
            # extract 'sender="MAZAK"'
            sender = "UNKNOWN"
            version = "UNKNOWN"
            
            import re
            sender_match = re.search(r'sender="([^"]+)"', xml_content)
            if sender_match:
                sender = sender_match.group(1)
                
            version_match = re.search(r'<Header[^>]+version="([^"]+)"', xml_content)
            if version_match:
                version = version_match.group(1)

            return Fingerprint(
                ip=ip,
                protocol="mtconnect",
                endpoint=url,
                confidence=0.9, # High confidence if we got valid XML response
                vendor=sender.upper() if sender != "UNKNOWN" else None,
                model="Unknown", # Model is hard to get from Header, sometimes in DeviceStream name
                controller_version=version,
                evidence={"sender": sender, "version": version}
            )

        except Exception as e:
            with open("/tmp/mtconnect_debug.txt", "a") as f:
                f.write(f"DEBUG: MTConnect Exception: {e}\n")
            logger.debug(f"MTConnect probe failed for {ip}:{port} - {e}")
            return None
