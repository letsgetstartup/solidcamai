import logging
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from typing import Optional
from simco_agent.drivers.common.models import Fingerprint

logger = logging.getLogger(__name__)

class MTConnectProbe:
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        """
        Probes an IP:Port for MTConnect compatibility.
        """
        async with aiohttp.ClientSession() as session:
            # Try /probe first (standard)
            url = f"http://{ip}:{port}/probe"
            fp = await self._try_endpoint(session, url, ip, port)
            if fp:
                return fp
                
            # Fallback to /current (some adapters don't implement probe)
            url = f"http://{ip}:{port}/current"
            fp = await self._try_endpoint(session, url, ip, port)
            if fp:
                return fp
                
        return None

    async def _try_endpoint(self, session, url: str, ip: str, port: int) -> Optional[Fingerprint]:
        try:
            async with session.get(url, timeout=self.timeout) as response:
                if response.status != 200:
                    return None
                    
                text = await response.text()
                return self._parse_mtconnect_header(text, ip, port, url)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None
        except Exception as e:
            logger.debug(f"MTConnect probe error for {url}: {e}")
            return None

    def _parse_mtconnect_header(self, xml_text: str, ip: str, port: int, url: str) -> Optional[Fingerprint]:
        try:
            # Strip namespaces to make parsing easier (hacky but robust for diverse adapters)
            # A better way is to handle namespaces properly, but for fingerprinting usually fine
            # We'll just ignore namespaces in find()
            
            root = ET.fromstring(xml_text)
            
            # Check if root is MTConnectDevices or MTConnectStreams
            if "MTConnect" not in root.tag:
                return None
            
            # Extract header info
            header = root.find(".//Header") # Use relative search
            if header is None:
                # Try finding direct child if namespace issue
                for child in root:
                    if "Header" in child.tag:
                        header = child
                        break
            
            # Extract device info
            # Usually under <Devices><Device>...
            # We search for the first Manufacturer/Model we can find
            
            manufacturer = self._find_text(root, ".//Manufacturer")
            model = self._find_text(root, ".//Model")
            serial = self._find_text(root, ".//SerialNumber")
            
            # If we found at least one of these or it's definitely MTConnect XML, we match
            confidence = 0.95
            
            base_url = f"http://{ip}:{port}"
            
            return Fingerprint(
                ip=ip,
                protocol="mtconnect",
                vendor=manufacturer,
                model=model,
                serial=serial,
                endpoint=base_url,
                confidence=confidence,
                evidence={"url": url, "xml_root": root.tag}
            )
            
        except ET.ParseError:
            return None
        except Exception as e:
            logger.warning(f"MTConnect XML parse error: {e}")
            return None

    def _find_text(self, root, path) -> Optional[str]:
        # Helper to find text ignoring namespaces if possible or just standard find
        # Since we didn't strip namespaces from string, find() might fail if not using {ns}Tag
        # Quick hack: search by tag name recursively
        tag_name = path.split("//")[-1]
        for elem in root.iter():
            if elem.tag.endswith(tag_name) or elem.tag.endswith("}" + tag_name):
                return elem.text
        return None
