import yaml
import logging
import hashlib
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class RuleEvaluator:
    """Loads and evaluates rules against telemetry batches."""
    
    def __init__(self, rules_path: str = "cloud/rules/ruleset.yaml"):
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, path: str) -> List[Dict[str, Any]]:
        try:
            with open(path, 'r') as f:
                content = yaml.safe_load(f)
                return content.get("rules", [])
        except Exception as e:
            logger.error(f"Rules: Failed to load {path}: {e}")
            return []

    def evaluate(self, record: Dict[str, Any], previous_state: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Evaluates a record against all rules. Returns derived EventRecords."""
        derived_events = []
        
        for rule in self.rules:
            event = None
            if rule["type"] == "threshold":
                event = self._eval_threshold(rule, record)
            elif rule["type"] == "state_change" and previous_state:
                event = self._eval_state_change(rule, record, previous_state)
            
            if event:
                derived_events.append(event)
                
        return derived_events

    def _eval_threshold(self, rule: Dict[str, Any], record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        metric_name = rule["metric"]
        metrics = record.get("metrics", {})
        if metric_name not in metrics:
            return None
            
        val = metrics[metric_name]
        threshold = rule["value"]
        triggered = False
        
        if rule["operator"] == ">" and val > threshold:
            triggered = True
        elif rule["operator"] == "<" and val < threshold:
            triggered = True
            
        if triggered:
            return self._create_derived_event(rule, record, f"Threshold {threshold} breached: {val}")
        return None

    def _eval_state_change(self, rule: Dict[str, Any], record: Dict[str, Any], prev: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current_status = record.get("status")
        previous_status = prev.get("status")
        
        if previous_status == rule["from"] and current_status == rule["to"]:
            return self._create_derived_event(rule, record, f"State change {rule['from']} -> {rule['to']} detected")
        return None

    def _create_derived_event(self, rule: Dict[str, Any], record: Dict[str, Any], message: str) -> Dict[str, Any]:
        # Deterministic Event ID for idempotency: tenant:site:machine:rule_id:record_timestamp
        seed = f"{record['tenant_id']}:{record['site_id']}:{record['machine_id']}:{rule['id']}:{record['timestamp']}"
        event_id = hashlib.sha256(seed.encode()).hexdigest()
        
        return {
            "event_id": event_id,
            "tenant_id": record["tenant_id"],
            "site_id": record["site_id"],
            "machine_id": record["machine_id"],
            "timestamp": record["timestamp"],
            "event_type": rule["event_type"],
            "severity": rule["severity"],
            "message": message,
            "rule_id": rule["id"],
            "source_record_id": record.get("record_id")
        }
