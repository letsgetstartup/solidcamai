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
from .fingerprint_hasher import generate_machine_id
from .selection import DriverSelector

logger = logging.getLogger(__name__)

class DiscoveryOrchestrator:
    def __init__(self, registry_path: str = None):
        self.registry_path = registry_path
        self.policy = DiscoveryPolicy() # Default, usually updated via ConfigManager
        self.driver_selector = DriverSelector()

    def update_policy(self, config: Dict[str, Any]):
        """Updates internal policy from cloud configuration."""
        # Config key from Cloud is 'discovery'
        discovery_cfg = config.get("discovery") or config.get("discovery_policy", {})
        
        if discovery_cfg:
            # Map Cloud Schema to Internal Policy Schema
            mapped_cfg = discovery_cfg.copy()
            
            # Map 'subnets' -> 'allowed_subnets'
            if "subnets" in discovery_cfg:
                mapped_cfg["allowed_subnets"] = discovery_cfg["subnets"]
                
            # Map 'protocols' -> 'port_probes' (Filter default probes)
            if "protocols" in discovery_cfg:
                allowed_protocols = set(discovery_cfg["protocols"])
                # Default probes map
                default_probes = {
                    "fanuc_focas": [8193],
                    "modbus": [502],
                    "opc_ua": [4840], # Normalized key
                    "opcua": [4840],  # Alias
                    "mtconnect": [7878],
                    "ethernetip": [44818]
                }
                filtered_probes = {}
                for proto in allowed_protocols:
                    if proto in default_probes:
                        filtered_probes[proto] = default_probes[proto]
                
                # If filtered_probes is empty but protocols were provided, it might mean known protocols 
                # but no port scan needed (e.g. passive only), or custom. 
                # For now we replace the active probe list.
                if filtered_probes:
                    mapped_cfg["port_probes"] = filtered_probes

            try:
                new_policy = DiscoveryPolicy(**mapped_cfg)
                self.policy = new_policy
                self.policy.log_decision()
            except Exception as e:
                logger.error(f"Failed to apply discovery policy: {e}")

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
            
            # Use normalized port dictionary
            port_map = self.policy.get_normalized_port_map()
            
            active_results = discover_active(
                subnets=subnets,
                port_map=port_map,
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

    async def run_fingerprinting(self, candidates: List[Dict[str, Any]]) -> List[Any]:
        """Runs async fingerprinting on candidates."""
        from .fingerprinting import FingerprintOrchestrator
        fp_orch = FingerprintOrchestrator()
        return await fp_orch.run(candidates)

    def save_fingerprints(self, fingerprints: List[Any]):
        """Updates registry with confirmed fingerprints."""
        if not fingerprints:
            return

        from dataclasses import asdict
        registry = load_registry(self.registry_path)
        existing = {m["ip"]: i for i, m in enumerate(registry)}
        updates = 0

        for fp in fingerprints:
            if fp.ip in existing:
                idx = existing[fp.ip]
                # 1. Generate Deterministic ID
                machine_hash = generate_machine_id(fp)
                
                # 2. Select Driver
                driver_match = self.driver_selector.select_driver(fp)
                
                # 3. Update Registry
                reg_entry = registry[idx]
                meta = reg_entry.get("metadata", {})
                
                # Store core identity
                meta["fingerprint"] = asdict(fp)
                meta["machine_hash"] = machine_hash
                
                # If driver found, promote to READY_TO_ENROLL or auto-configure
                if driver_match:
                    meta["selected_driver"] = {
                        "name": driver_match.manifest.name,
                        "version": driver_match.manifest.version,
                        "score": driver_match.score
                    }
                    reg_entry["driver_id"] = driver_match.manifest.name # Top level linkage
                    
                    if fp.confidence > 0.8:
                        reg_entry["status"] = "READY_TO_ENROLL"
                        reg_entry["vendor"] = fp.vendor or reg_entry.get("vendor")
                        # Use deterministic hash as machine_id if not already assigned manually
                        # But be careful not to break existing ID if it was enrolled logic.
                        # For new machines:
                        if reg_entry.get("source") != "manual_portal":
                            reg_entry["machine_id"] = machine_hash

                reg_entry["metadata"] = meta
                updates += 1
        
        if updates > 0:
            save_registry(registry, self.registry_path)
            logger.info(f"Orchestrator: Updated {updates} machines with fingerprints & drivers")

    def _update_registry(self, candidates: List[Dict[str, Any]]):
        registry = load_registry(self.registry_path)
        existing = {m["ip"]: i for i, m in enumerate(registry)}

        # Use IP as machine_id if unknown
        for c in candidates:
            ip = c["ip"]
            # Extract protocols from candidates if present
            protocols = []
            if "protocol_candidates" in c:
                for pc in c["protocol_candidates"]:
                    protocols.extend(pc.get("protocols", []))
            protocols = list(set(protocols))

            if ip not in existing:
                entry = {
                    "machine_id": ip,
                    "ip": ip,
                    "vendor": c.get("vendor", "UNKNOWN"),
                    "status": "DISCOVERED",
                    "source": c["source"],
                    "last_seen": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
                if protocols:
                    entry["metadata"] = entry.get("metadata", {})
                    entry["metadata"]["protocols"] = protocols
                
                registry.append(entry)
            else:
                idx = existing[ip]
                registry[idx]["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                registry[idx]["status"] = "REACHABLE"
                # Update metadata if we found new protocols
                if protocols:
                    meta = registry[idx].get("metadata", {})
                    current_protos = set(meta.get("protocols", []))
                    current_protos.update(protocols)
                    meta["protocols"] = list(current_protos)
                    registry[idx]["metadata"] = meta

        save_registry(registry, self.registry_path)
        logger.info(f"Orchestrator: Machine registry updated with {len(candidates)} candidates")


