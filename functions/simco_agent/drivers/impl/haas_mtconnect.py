import logging
import asyncio
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional
from simco_agent.drivers.driver_interface import DriverInterface
from simco_agent.drivers.common.models import TelemetryPoint, SignalQuality

logger = logging.getLogger(__name__)

class HaasMTConnectDriver(DriverInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ip = config.get("ip")
        self.port = config.get("port", 7878)
        self.base_url = f"http://{self.ip}:{self.port}"
        self.timeout = config.get("timeout", 5)
        self._connected = False

    async def connect(self) -> bool:
        # Check if endpoint is reachable
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None, 
                lambda: requests.get(f"{self.base_url}/probe", timeout=self.timeout)
            )
            self._connected = (resp.status_code == 200)
        except Exception as e:
            logger.warning(f"Haas MTConnect connect failed: {e}")
            self._connected = False
        return self._connected

    async def disconnect(self):
        self._connected = False

    async def collect_metrics(self) -> List[TelemetryPoint]:
        """
        Polls /current and parses Haas specific tags.
        """
        points = []
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: requests.get(f"{self.base_url}/current", timeout=self.timeout)
            )
            
            if resp.status_code != 200:
                logger.error(f"Haas MTConnect poll failed: {resp.status_code}")
                return []
                
            xml_content = resp.text
            # Remove namespace for easier parsing
            xml_content = self._strip_namespaces(xml_content)
            root = ET.fromstring(xml_content)
            
            # Find Device Stream
            # Usually /current returns Streams -> DeviceStream -> ComponentStream -> Events/Samples
            
            # We will search by Tag Name or specific DataItemId if we know them.
            # Usually Haas aligns with standard MTConnect names.
            
            ts = datetime.utcnow().isoformat()
            
            # 1. Execution State
            # Path: //Events/Execution or //Events/DataItem[@type='EXECUTION'] or just filtering by name
            # Often dataItemId="exec" name="execution"
            exec_node = self._find_first(root, ".//Execution")
            if exec_node is not None:
                points.append(TelemetryPoint(
                    name="execution_state",
                    value=exec_node.text,
                    timestamp=ts
                ))
                
            # 2. Controller Mode
            control_node = self._find_first(root, ".//ControllerMode")
            if control_node is not None:
                points.append(TelemetryPoint(
                    name="controller_mode",
                    value=control_node.text,
                    timestamp=ts
                ))
            
            # 3. Spindle Speed
            # Path: //Samples/SpindleSpeed or name="spindle_speed"
            # Note: Might be Sload, Sspeed, etc. searching by name/type is safer.
            spindle_node = self._find_first_by_tag_or_attrib(root, "SpindleSpeed", "spindle_speed")
            if spindle_node is not None:
                val = self._safe_float(spindle_node.text)
                if val is not None:
                     points.append(TelemetryPoint(
                        name="spindle_speed",
                        value=val,
                        timestamp=ts
                    ))
            
            # 4. Path Feedrate
            # PathFeedrate
            feed_node = self._find_first_by_tag_or_attrib(root, "PathFeedrate", "path_feedrate")
            if feed_node is not None:
                val = self._safe_float(feed_node.text)
                if val is not None:
                    points.append(TelemetryPoint(
                        name="path_feedrate",
                        value=val,
                        timestamp=ts
                    ))
            
            # 5. Program Name
            # Program
            prog_node = self._find_first(root, ".//Program")
            if prog_node is not None:
                points.append(TelemetryPoint(
                    name="program_name",
                    value=prog_node.text,
                    timestamp=ts
                ))
                
            return points

        except Exception as e:
            logger.error(f"Error collecting metrics from Haas: {e}")
            return []

    def _strip_namespaces(self, xml_string):
        # Naive strip: remove xmlns attributes
        # Better: use Regex to remove xmlns="..."
        import re
        return re.sub(r'\sxmlns="[^"]+"', '', xml_string, count=1)

    def _find_first(self, root, xpath):
        return root.find(xpath)
        
    def _find_first_by_tag_or_attrib(self, root, tag, name_substr):
        # Try finding by explicit tag
        node = root.find(f".//{tag}")
        if node is not None:
            return node
            
        # Try finding by name attribute if tag name usage varies
        # e.g. <DataItem type="SPINDLE_SPEED" name="spindle_speed">
        # This is expensive (iter) but MTConnect trees are small enough usually
        for elem in root.iter():
            if name_substr in elem.get('name', '').lower():
                return elem
        return None

    def _safe_float(self, value):
        try:
            return float(value)
        except:
            return None
