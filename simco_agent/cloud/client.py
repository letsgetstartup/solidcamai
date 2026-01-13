import logging
import aiohttp
import asyncio
import json
from typing import List
from dataclasses import asdict
from simco_agent.drivers.common.models import TelemetryPoint
from simco_agent.cloud.auth import AuthProvider

logger = logging.getLogger(__name__)

class CloudClient:
    def __init__(self, base_url: str, auth_provider: AuthProvider):
        self.base_url = base_url.rstrip("/")
        self.auth = auth_provider

    async def send_telemetry(self, points: List[TelemetryPoint]) -> bool:
        """
        Sends points to the ingestion endpoint.
        Returns True if successful.
        """
        if not points:
            return True

        try:
            token = await self.auth.get_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = [asdict(p) for p in points]
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v1/ingest"
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    if response.status == 200 or response.status == 201:
                        logger.debug(f"Successfully uploaded {len(points)} points")
                        return True
                    else:
                        logger.warning(f"Upload failed: {response.status} - {await response.text()}")
                        return False

        except Exception as e:
            logger.error(f"Error sending telemetry: {e}")
            return False
