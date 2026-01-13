import json
import os
import time
import logging
from typing import List, Dict, Any
from .policy import DiscoveryPolicy
from .passive import discover_passive
from .active import discover_active
from simco_agent.config import settings
from simco_agent.core.registry import load_registry, save_registry

logger = logging.getLogger(__name__)

class DiscoveryOrchestrator:
    def __init__(self, registry_path: str = None):
        self.registry_path = registry_path
        self.policy = DiscoveryPolicy() # Default, usually updated via ConfigManager

    def update_policy(self, config: Dict[str, Any]):
        """Updates internal policy from cloud configuration."""
        discovery_cfg = config.get("discovery_policy", {})
        if discovery_cfg:
            new_policy = DiscoveryPolicy(**discovery_cfg)
            self.policy = new_policy
            self.policy.log_decision()

    def run_discovery_cycle(self) -> List[Dict[str, Any]]:
        """Runs the orchestrated discovery cycle according to current policy."""
        from simco_agent.observability.metrics import edge_metrics
        start_time = time.time()
        all_candidates = []

        # 1. Passive Discovery
        if self.policy.is_passive_allowed():
            passive_results = discover_passive()
            all_candidates.extend(passive_results)

        # 2. Active Discovery
        if self.policy.is_active_allowed():
            # Extract subnets from policy or default to common local ranges if empty
            subnets = self.policy.allowed_subnets or [settings.SCAN_SUBNET]
            active_results = discover_active(
                subnets=subnets,
                ports=self.policy.port_probes,
                rate_limit_pps=self.policy.active_rate_limit_pps
            )
            # Merge while avoiding duplicates (prefer active for higher confidence)
            active_ips = {r["ip"] for r in active_results}
            all_candidates = [c for c in all_candidates if c["ip"] not in active_ips]
            all_candidates.extend(active_results)

        # 3. Process candidates and update registry
        self._update_registry(all_candidates)
        
        # Emit Metrics
        duration = time.time() - start_time
        edge_metrics.gauge("edge.discovery.duration_sec", duration)
        edge_metrics.gauge("edge.discovery.hosts_found", len(all_candidates))
        
        return all_candidates

    def _update_registry(self, candidates: List[Dict[str, Any]]):
        registry = load_registry(self.registry_path)
        existing = {m["ip"]: i for i, m in enumerate(registry)}

        # Use IP as machine_id if unknown
        for c in candidates:
            ip = c["ip"]
            if ip not in existing:
                registry.append({
                    "machine_id": ip,
                    "ip": ip,
                    "vendor": c.get("vendor", "UNKNOWN"),
                    "status": "DISCOVERED",
                    "source": c["source"],
                    "last_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                })
            else:
                idx = existing[ip]
                registry[idx]["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                registry[idx]["status"] = "REACHABLE"

        save_registry(registry, self.registry_path)
        logger.info(f"Orchestrator: Machine registry updated with {len(candidates)} candidates")


