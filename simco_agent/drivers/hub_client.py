import logging
import aiohttp
import json
import os
from typing import List, Optional
from simco_agent.drivers.common.models import DriverManifest
from simco_agent.drivers.selection import DriverSelector

logger = logging.getLogger(__name__)

class DriverHubClient:
    def __init__(self, hub_url: str):
        self.hub_url = hub_url

    async def fetch_manifests(self) -> List[DriverManifest]:
        """
        Fetches the master manifest list from the Driver Hub.
        """
        manifests = []
        try:
            logger.info(f"HubClient: Fetching manifests from {self.hub_url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.hub_url, timeout=10) as response:
                    if response.status != 200:
                        logger.warning(f"HubClient: Failed to fetch manifest. Status: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    # Parse JSON list into objects
                    if isinstance(data, list):
                        for item in data:
                            try:
                                # Convert item dict to DriverManifest
                                # Ensure required fields match
                                m = DriverManifest(
                                    name=item.get("name"),
                                    version=item.get("version"),
                                    description=item.get("description", ""),
                                    protocol=item.get("protocol", "unknown"),
                                    match_rules=item.get("match_rules", [])
                                )
                                manifests.append(m)
                            except Exception as e:
                                logger.warning(f"HubClient: Failed to parse manifest item: {e}")
                                
            return manifests
            
        except Exception as e:
            logger.error(f"HubClient: Network error fetching manifests: {e}")
            return []

    async def sync_to_selector(self, selector: DriverSelector):
        """
        Fetches manifests and registers them with the selector.
        """
        manifests = await self.fetch_manifests()
        count = 0
        for m in manifests:
            selector.register_driver(m)
            count += 1
        
        logger.info(f"HubClient: Synced {count} drivers to selector")
