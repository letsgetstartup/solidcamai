import logging
import re
from typing import List, Optional
from simco_agent.drivers.common.models import Fingerprint, DriverManifest, DriverMatch

logger = logging.getLogger(__name__)

class DriverSelector:
    def __init__(self):
        # In the future, this will load from a directory of YAMLs
        self.manifests = self._load_builtin_manifests()

    def _load_builtin_manifests(self) -> List[DriverManifest]:
        return [
            DriverManifest(
                name="haas_mtconnect",
                version="1.0.0",
                description="Driver for Haas NGC machines via MTConnect",
                protocol="mtconnect",
                match_rules=[{"vendor": "HAAS.*"}],
                checksum="67fb18366ca67a64a99f1417990e08a2e0d76ae867e217a80f0809a06caa1067"
            ),
            DriverManifest(
                 name="mazak-mtconnect",
                 version="1.0.0",
                 description="Driver for Mazak machines via MTConnect",
                 protocol="mtconnect",
                 match_rules=[{"vendor": "MAZAK.*"}]
            ),
            DriverManifest(
                name="siemens_opcua",
                version="1.0.0",
                description="Driver for Siemens 840D sl/828D via OPC UA",
                protocol="opc_ua",
                match_rules=[{"vendor": "SIEMENS.*"}],
                checksum="f8a9a00addecb410e8540fae7e075fc5d3cdf526b9ab8f2a0ff28ec15cc1e06b"
            ),
            DriverManifest(
                name="fanuc-focas",
                version="1.0.0",
                description="Driver for Fanuc i-Series via FOCAS2",
                protocol="fanuc_focas",
                match_rules=[{"vendor": "FANUC.*"}]
            ),
             DriverManifest(
                name="generic-mtconnect",
                version="1.0.0",
                description="Generic MTConnect Driver",
                protocol="mtconnect",
                match_rules=[{}] # Match all mtconnect if protocol aligns
            )
        ]

    def select_driver(self, fp: Fingerprint) -> Optional[DriverMatch]:
        """
        Selects the best driver for a given fingerprint.
        """
        best_match = None
        best_score = -1.0
        
        for manifest in self.manifests:
            score = self._calculate_match_score(fp, manifest)
            if score > best_score and score > 0.0:
                best_match = DriverMatch(manifest=manifest, score=score, reasons=[])
                best_score = score
                
        if best_match:
            logger.info(f"Selected driver {best_match.manifest.name} (Score: {best_score}) for {fp.ip}")
            
        return best_match

    def _calculate_match_score(self, fp: Fingerprint, manifest: DriverManifest) -> float:
        # 1. Protocol Mismatch = 0
        if manifest.protocol != fp.protocol:
            return 0.0
            
        # 2. Rule Matching
        score = 0.5 # Base score for protocol match
        
        for rule in manifest.match_rules:
            # Check Vendor
            if "vendor" in rule and fp.vendor:
                if re.match(rule["vendor"], fp.vendor, re.IGNORECASE):
                    score += 0.4 # Strong bump for Vendor match
                else:
                    # If vendor rule exists but doesn't match, this rule fails.
                    # But maybe another rule passes? For now, we assume OR logic between rules
                    pass
            
            # Check Model
            if "model" in rule and fp.model:
                 if re.match(rule["model"], fp.model, re.IGNORECASE):
                    score += 0.1
                    
        return min(score, 1.0)
