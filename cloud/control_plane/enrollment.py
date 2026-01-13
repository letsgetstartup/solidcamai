import random
import string
import uuid
import datetime
import logging
from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from .db import AuditLog, Gateway, GatewayStatus
from .crud import create_gateway, get_gateway

logger = logging.getLogger(__name__)

class ClaimCodeManager:
    """
    Manages short-lived claim codes in memory (MVP).
    In production, use Redis.
    """
    def __init__(self):
        # code -> {"gateway_temp_id": str, "created_at": datetime, "status": "WAITING"|"CLAIMED", "site_id": str, "authorized_gateway_id": str}
        self._codes: Dict[str, Dict] = {} 
        self._temp_ids: Dict[str, str] = {} # temp_id -> code

    def generate_code(self) -> Tuple[str, str]:
        """
        Generates a 6-digit code and a temporary poll token.
        Returns (code, poll_token).
        """
        code = "".join(random.choices(string.digits, k=6))
        poll_token = str(uuid.uuid4())
        
        self._codes[code] = {
            "poll_token": poll_token,
            "created_at": datetime.datetime.utcnow(),
            "status": "WAITING",
            "site_id": None,
            "final_gateway_id": None
        }
        self._temp_ids[poll_token] = code
        return code, poll_token

    def claim_code(self, code: str, site_id: str, tenant_id: str) -> bool:
        """
        User claims the code. Maps it to a site.
        """
        if code not in self._codes:
            return False
            
        entry = self._codes[code]
        # Check expiry (e.g. 15 mins)
        if (datetime.datetime.utcnow() - entry["created_at"]).total_seconds() > 900:
            del self._codes[code]
            return False
            
        entry["status"] = "CLAIMED"
        entry["site_id"] = site_id
        entry["tenant_id"] = tenant_id
        # Pre-generate a Final Gateway ID now? Or wait for Provision step?
        # Let's generate it now so we can link it
        entry["final_gateway_id"] = f"gw-{uuid.uuid4().hex[:8]}"
        
        return True

    def get_status(self, poll_token: str) -> Optional[Dict]:
        code = self._temp_ids.get(poll_token)
        if not code or code not in self._codes:
            return None
        return self._codes[code]

enrollment_manager = ClaimCodeManager()

async def register_claimed_gateway(db: AsyncSession, code: str, display_name: str = "New Gateway") -> Optional[Gateway]:
    """
    Finalizes enrollment in DB.
    """
    entry = enrollment_manager._codes.get(code)
    if not entry or entry["status"] != "CLAIMED":
        return None
        
    # Create Real Gateway Record
    gw = await create_gateway(
        db, 
        gateway_id=entry["final_gateway_id"],
        tenant_id=entry["tenant_id"],
        site_id=entry["site_id"],
        display_name=display_name
    )
    
    # Audit Log
    log = AuditLog(
        action="GATEWAY_ENROLLED",
        actor_id="SYSTEM",
        target_id=gw.gateway_id,
        details=f"Enrolled via claim code {code}"
    )
    db.add(log)
    await db.commit()
    
    # Cleanup
    # del enrollment_manager._codes[code] # Keep strictly for ACK? Or delete now.
    
    return gw
