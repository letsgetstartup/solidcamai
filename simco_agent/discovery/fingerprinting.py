import logging
import asyncio
from typing import List, Dict, Any, Optional
from simco_agent.drivers.common.models import Fingerprint

logger = logging.getLogger(__name__)

class FingerprintOrchestrator:
    """
    Orchestrates the fingerprinting process for discovered candidates.
    Matches protocol hints to specific probes and aggregates results.
    """
    def __init__(self):
        # In future PRs, we will inject probe strategies here
        pass

    async def run(self, candidates: List[Dict[str, Any]]) -> List[Fingerprint]:
        """
        Runs fingerprinting on a list of discovery candidates.
        """
        results = []
        if not candidates:
            return results

        logger.info(f"Fingerprint: processing {len(candidates)} candidates")
        
        # We can parallelize this using asyncio.gather in the future
        for c in candidates:
            fp = await self._fingerprint_candidate(c)
            if fp:
                results.append(fp)
                
        logger.info(f"Fingerprint: resolved {len(results)} identities")
        return results

    async def _fingerprint_candidate(self, candidate: Dict[str, Any]) -> Optional[Fingerprint]:
        """
        Attempts to fingerprint a single candidate.
        """
        ip = candidate["ip"]
        protocol_candidates = candidate.get("protocol_candidates", [])
        
        # If no protocol candidates (e.g. from passive scan or old active scan), skip or use generic
        if not protocol_candidates:
            return None

        # Prioritize protocols (could be policy driven)
        # For now, just try the first valid one we have a probe for
        
        # Placeholder logic until PRs 04-06 implement real probes
        # We simulate a "probe attempt" based on the hints
        
        best_fp = None
        
        for pc in protocol_candidates:
            # Each pc is {"port": 123, "protocols": ["focas"]}
            port = pc["port"]
            protos = pc.get("protocols", [])
            
            for proto in protos:
                fp = await self._run_probe_placeholder(proto, ip, port)
                if fp and (best_fp is None or fp.confidence > best_fp.confidence):
                    best_fp = fp
        
        return best_fp

    async def _run_probe_placeholder(self, protocol: str, ip: str, port: int) -> Optional[Fingerprint]:
        """
        Executes the appropriate probe for the given protocol.
        """
        try:
            if protocol == "mtconnect":
                from .probes.mtconnect import MTConnectProbe
                probe = MTConnectProbe()
                return await probe.run(ip, port)

            if protocol == "opc_ua" or protocol == "opcua":
                from .probes.opcua import OPCUAProbe
                probe = OPCUAProbe()
                return await probe.run(ip, port)

            if protocol == "fanuc_focas" or protocol == "focas":
                from .probes.focas import FocasProbe
                probe = FocasProbe()
                return await probe.run(ip, port)
                
            # Fallback for other protocols
            # Simulate network I/O
            # await asyncio.sleep(0.01) 
            
            # Return a distinct fingerprint to prove the plumbing works
            return Fingerprint(
                ip=ip,
                protocol=protocol,
                endpoint=f"{protocol}://{ip}:{port}",
                confidence=0.5, # moderate confidence from just "port open"
                evidence={"port_open": port}
            )
        except Exception as e:
            logger.warning(f"Fingerprint probe failed for {protocol}@{ip}:{port}: {e}")
            return None
