import logging
import json
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class NotificationDispatcher:
    """Dispatches alerts to various connectors (Webhook, Email)."""
    
    def __init__(self):
        self.notification_log = []
        self.rate_limits: Dict[str, float] = {}  # {key: last_sent_timestamp}
        self.MIN_INTERVAL = 60  # Rate limit: 1 alert per machine per minute

    async def dispatch(self, event: Dict[str, Any]):
        """Dispatches an event to all configured connectors."""
        tenant_id = event.get("tenant_id")
        site_id = event.get("site_id")
        machine_id = event.get("machine_id")
        event_type = event.get("event_type")
        
        # 1. Rate Limiting
        limit_key = f"{tenant_id}:{site_id}:{machine_id}:{event_type}"
        now = time.time()
        if now - self.rate_limits.get(limit_key, 0) < self.MIN_INTERVAL:
            logger.debug(f"Notify: Rate limited {limit_key}")
            return

        self.rate_limits[limit_key] = now
        
        # 2. Connector Logic
        logger.info(f"Notify: Dispatching {event_type} for {machine_id}")
        
        from simco_agent.observability.metrics import cloud_metrics
        try:
            # Mock Webhook
            await self._send_webhook(event)
            # Mock Email
            await self._send_email(event)
            
            cloud_metrics.counter("cloud.notifications.sent_count", 1, labels={"event_type": event_type})
        except Exception as e:
            logger.error(f"Notify: Dispatch failed: {e}")
            cloud_metrics.counter("cloud.notifications.failed_count", 1, labels={"event_type": event_type, "error": str(type(e).__name__)})

        # 3. Audit Logging
        self._log_notification(event)

    async def _send_webhook(self, event: Dict[str, Any]):
        # In production, use a library like 'httpx' or 'requests'
        logger.debug(f"Notify [Webhook]: POST to configured endpoint for {event.get('machine_id')}")

    async def _send_email(self, event: Dict[str, Any]):
        logger.debug(f"Notify [Email]: Sending alert for {event.get('machine_id')} to subscribers")

    def _log_notification(self, event: Dict[str, Any]):
        audit_entry = {
            "timestamp": time.time(),
            "event_id": event.get("event_id"),
            "tenant_id": event.get("tenant_id"),
            "machine_id": event.get("machine_id"),
            "status": "SENT"
        }
        self.notification_log.append(audit_entry)
        # In production, write to a DB
        logger.info(f"Notify [Audit]: {json.dumps(audit_entry)}")

# Singleton instance
dispatcher = NotificationDispatcher()
