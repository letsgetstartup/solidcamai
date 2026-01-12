import asyncio
import logging
from typing import Callable, List, Dict, Any, Awaitable

logger = logging.getLogger(__name__)

class EventBus:
    """Generic interface for an event bus."""
    async def publish(self, records: List[Dict[str, Any]]):
        raise NotImplementedError

    def subscribe(self, handler: Callable[[List[Dict[str, Any]]], Awaitable[None]]):
        raise NotImplementedError

class LocalBus(EventBus):
    """In-process implementation of the event bus for development and testing."""
    def __init__(self):
        self.handlers: List[Callable[[List[Dict[str, Any]]], Awaitable[None]]] = []

    async def publish(self, records: List[Dict[str, Any]]):
        if not records:
            return
        logger.debug(f"LocalBus: Publishing {len(records)} records")
        for handler in self.handlers:
            try:
                await handler(records)
            except Exception as e:
                logger.error(f"LocalBus: Handler failed: {e}")

    def subscribe(self, handler: Callable[[List[Dict[str, Any]]], Awaitable[None]]):
        self.handlers.append(handler)
        logger.debug("LocalBus: New subscriber added")

# Singleton instance for local/dev use
bus = LocalBus()
