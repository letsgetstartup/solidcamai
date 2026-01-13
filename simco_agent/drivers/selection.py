import logging
import re
from typing import List, Dict, Optional
from simco_agent.drivers.common.models import Fingerprint, DriverManifest, DriverMatch

logger = logging.getLogger(__name__)

class DriverSelector:
    def __init__(self):
        self._manifests: List[DriverManifest] = []

    def register_driver(self, manifest: DriverManifest):
        self._manifests.append(manifest)

    def select_best_match(self, fingerprint: Fingerprint) -> Optional[DriverMatch]:
        matches = self.find_matches(fingerprint)
        if not matches:
            return None
        # Return match with highest score
        return max(matches, key=lambda m: m.score)

    def find_matches(self, fingerprint: Fingerprint) -> List[DriverMatch]:
        matches = []
        for manifest in self._manifests:
            match = self._evaluate(manifest, fingerprint)
            if match.score > 0:
                matches.append(match)
        return matches

    def _evaluate(self, manifest: DriverManifest, fp: Fingerprint) -> DriverMatch:
        reasons = []
        score = 0.0

        # 1. Protocol Match (Gatekeeper)
        # If manifest specifies protocol, it must match
        if manifest.protocol and manifest.protocol != "unknown":
            if manifest.protocol.lower() != fp.protocol.lower():
                return DriverMatch(manifest, 0.0, ["Protocol mismatch"])
            score += 0.4
            reasons.append(f"Protocol '{fp.protocol}' matched")

        # 2. Rule evaluation
        # Manifest can have multiple rules. If ANY rule matches, we take the best score from rules.
        # If no rules, we rely on protocol score.
        
        best_rule_score = 0.0
        
        if not manifest.match_rules:
            # Generic driver for protocol
            if score > 0:
                reasons.append("Generic protocol match")
        else:
            rule_matched = False
            for rule in manifest.match_rules:
                rule_score = 0.0
                matched_aspects = []
                
                # Check Vendor
                if "vendor" in rule and fp.vendor:
                    if re.search(rule["vendor"], fp.vendor, re.IGNORECASE):
                        rule_score += 0.3
                        matched_aspects.append("Vendor")
                
                # Check Model
                if "model" in rule and fp.model:
                    if re.search(rule["model"], fp.model, re.IGNORECASE):
                        rule_score += 0.3
                        matched_aspects.append("Model")
                
                # Check Controller
                if "controller" in rule and fp.controller_version:
                    if re.search(rule["controller"], fp.controller_version, re.IGNORECASE):
                        rule_score += 0.1
                        matched_aspects.append("Controller")

                # If rule contained criteria but nothing matched, it failed this rule
                if rule and rule_score == 0.0:
                    continue

                if rule_score > best_rule_score:
                    best_rule_score = rule_score
                    if matched_aspects:
                        reasons.append(f"Rule match: {', '.join(matched_aspects)}")
                    rule_matched = True
            
            # If rules exist but none matched, we treat this as a non-match
            # (Prevent specific drivers from claiming generic devices solely on protocol)
            if not rule_matched:
                return DriverMatch(manifest, 0.0, ["Specific rules failed"])

        total_score = min(score + best_rule_score, 1.0)

        total_score = min(score + best_rule_score, 1.0)
        
        return DriverMatch(manifest, total_score, reasons)
