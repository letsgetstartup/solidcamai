import logging
import asyncio
import time
from typing import Optional

logger = logging.getLogger(__name__)

class AuthProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0
        
    async def get_token(self) -> str:
        """
        Returns a valid Bearer token.
        Authenticates if cached token is expired or missing.
        """
        current_time = time.time()
        if self._cached_token and current_time < self._token_expiry:
            return self._cached_token
            
        return await self._authenticate()
        
    async def _authenticate(self) -> str:
        # Mock implementation for offline environment
        # In prod: POST /api/auth/login with api_key -> returns JWT
        # For now, just return a mock token
        logger.info("Authenticating with Cloud Portal...")
        
        # Simulate network delay
        # await asyncio.sleep(0.1)
        
        self._cached_token = f"mock-jwt-token-{int(time.time())}"
        self._token_expiry = time.time() + 3600 # 1 hour
        return self._cached_token
