import logging
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Any
from simco_agent.drivers.common.base_driver import DriverBase
from simco_agent.drivers.common.models import TelemetryPoint, SignalQuality
from simco_agent.drivers.common.normalize import normalize_execution_state

logger = logging.getLogger(__name__)

class MTConnectDriver(DriverBase):
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._connected = False
        self._namespaces = {'m': 'urn:mtconnect.org:MTConnectStreams:1.3'} 
        # Note: namespaces are annoying in MTConnect, might need to handle dynamically

    async def connect(self) -> bool:
        """
        Check if we can reach the agent.
        """
        try:
            url = f"{self.endpoint}/current"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        self._connected = True
                        return True
                    else:
                        logger.warning(f"MTConnect connect failed with status {response.status}")
                        return False
        except Exception as e:
            logger.error(f"MTConnect connect error: {e}")
            self._connected = False
            return False

    async def disconnect(self):
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    async def sample(self) -> List[TelemetryPoint]:
        points = []
        try:
            url = f"{self.endpoint}/current"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status != 200:
                        self._connected = False
                        return []
                    
                    xml_text = await response.text()
                    points = self._parse_streams(xml_text)
                    self._connected = True # re-confirm connection
                    return points

        except Exception as e:
            logger.error(f"MTConnect sample failed: {e}")
            self._connected = False
            return []

    def _parse_streams(self, xml_text: str) -> List[TelemetryPoint]:
        points = []
        try:
            # Strip namespaces to make parsing easier (hacky but effective for varied versions)
            # A more robust way is to handle Namespaces properly, but MTConnect usage is inconsistent
            # Let's try to use regex or just ignore namespace prefix in findall if possible? 
            # ElementTree requires namespace uri.
            
            # Simple hack: remove xmlns attributes before parsing? No, that's slow on big strings.
            # Better: iter parse and ignore tag prefix.
            
            root = ET.fromstring(xml_text)
            
            # Helper to strip namespace from tag
            def strip_ns(tag):
                return tag.split('}', 1)[1] if '}' in tag else tag

            # Scan all elements. This is O(N) but safer than assuming structure.
            # We look for specific types we care about.
            
            for elem in root.iter():
                tag_name = strip_ns(elem.tag)
                # Attributes
                name = elem.get('name')
                data_item_type = elem.get('type')
                print(f"DEBUG: Tag={tag_name}, Type={data_item_type}, Value={elem.text}") 
                category = elem.get('category') # EVENT, SAMPLE, CONDITION
                value = elem.text
                
                # If we don't have a value, skip
                if value is None: 
                    continue
                    
                # Logic: Check tag name primarily
                
                # 1. Execution State
                if tag_name == "Execution" or data_item_type == "EXECUTION":
                    points.append(TelemetryPoint(
                        name="execution_state",
                        value=normalize_execution_state(value),
                        timestamp=elem.get('timestamp', "")
                    ))
                
                # 2. Availability
                elif tag_name == "Availability" or data_item_type == "AVAILABILITY":
                    points.append(TelemetryPoint(
                        name="availability",
                        value=value.upper(),
                        timestamp=elem.get('timestamp', "")
                    ))
                    
                # 3. Controller Mode
                elif tag_name == "ControllerMode" or data_item_type == "CONTROLLER_MODE":
                    points.append(TelemetryPoint(
                        name="controller_mode",
                        value=value.upper(),
                        timestamp=elem.get('timestamp', "")
                    ))
                
                # 4. Spindle Speed (RotaryVelocity)
                elif tag_name == "RotaryVelocity" or data_item_type == "ROTARY_VELOCITY":
                     # Check subtype if needed, but usually main value is fine
                    if elem.get('subType') == "ACTUAL" or not elem.get('subType'):
                        try:
                            v = float(value)
                            points.append(TelemetryPoint(
                                name="spindle_speed",
                                value=v,
                                timestamp=elem.get('timestamp', "")
                            ))
                        except: pass
                
                # 5. Path Feedrate
                elif tag_name == "PathFeedrate" or data_item_type == "PATH_FEEDRATE":
                    if elem.get('subType') == "ACTUAL" or not elem.get('subType'):
                        try:
                            v = float(value)
                            points.append(TelemetryPoint(
                                name="path_feedrate",
                                value=v,
                                timestamp=elem.get('timestamp', "")
                            ))
                        except: pass
                
                # 6. Part Count
                elif tag_name == "PartCount" or data_item_type == "PART_COUNT":
                     try:
                        v = int(value)
                        points.append(TelemetryPoint(
                            name="part_count",
                            value=v,
                            timestamp=elem.get('timestamp', "")
                        ))
                     except: pass
                     
                # 7. Program
                elif tag_name == "Program" or data_item_type == "PROGRAM":
                    points.append(TelemetryPoint(
                        name="program_name",
                        value=value,
                        timestamp=elem.get('timestamp', "")
                    ))

        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}")
        except Exception as e:
            logger.error(f"MTConnect parsing error: {e}")
            import traceback
            traceback.print_exc()
            
        return points
