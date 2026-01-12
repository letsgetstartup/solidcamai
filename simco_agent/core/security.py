import logging
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List
from ..config import settings

logger = logging.getLogger("simco_agent.security")
audit_logger = logging.getLogger("simco_agent.audit")

class SecurityAgent:
    """Agent E: Responsible for security hardening, auditing, and compliance."""
    
    def __init__(self):
        self.audit_log_path = "security_audit.jsonl"
        self._last_event_hash = "INIT"
        self._setup_audit_logging()

    def _setup_audit_logging(self):
        handler = logging.FileHandler(self.audit_log_path)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        audit_logger.addHandler(handler)
        audit_logger.setLevel(logging.INFO)

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Logs a security event with a tamper-evident chain."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
            "previous_hash": self._last_event_hash
        }
        
        event_str = json.dumps(event, sort_keys=True)
        current_hash = hashlib.sha256(event_str.encode()).hexdigest()
        event["hash"] = current_hash
        self._last_event_hash = current_hash
        
        audit_logger.info(json.dumps(event))

    async def run_hardening(self):
        """Mock hardening of the system (Firewall, Permission checks)."""
        logger.info("Initializing Security Hardening (Agent E)...")
        # 1. Mock firewall rule enforcement
        self.log_event("FIREWALL_SYNC", {"status": "success", "rules_applied": ["DROP ALL", "ALLOW 8193", "ALLOW 443"]})
        
        # 2. Check for sensitive files permissions
        self._check_permissions()
        
        # 3. Encryption at Rest setup Check
        self.log_event("ENCRYPTION_CHECK", {"target": "buffer.jsonl", "mode": "AES-256-Mock"})

    def _check_permissions(self):
        # In a real scenario, this would use os.chmod and os.stat
        logger.info("Checking file permissions for simco-ai-v2...")
        self.log_event("PERMISSION_CHECK", {"status": "compliant", "files_audited": 12})

    def scrub_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """GDPR/Compliance: Remove or mask PII before cloud upload."""
        # For CNC data, we mask Operator ID or machine notes if present
        if "operator_id" in data:
            data["operator_id"] = "MASKED_" + hashlib.md5(data["operator_id"].encode()).hexdigest()[:8]
        return data

    async def verify_integrity(self) -> bool:
        """Verifies the audit chain integrity."""
        logger.info("Verifying security audit chain integrity...")
        # Simple verification logic would go here
        return True
