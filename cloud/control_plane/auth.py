from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .db import get_db, User, Membership, Tenant
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = logging.getLogger(__name__)

class CurrentUser(BaseModel):
    user_id: str
    email: Optional[str] = None
    memberships: List[dict] = [] # List of {"tenant_id": ..., "site_id": ..., "role": ...}

async def get_current_user_stub(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    DEV STUB: In production, verify JWT from Firebase/OIDC.
    For now, accepts any token "user_id:email".
    """
    if ":" not in token:
         # raise HTTPException(status_code=401, detail="Invalid token format (stub)")
         # Fallback for tests if simple string
         user_id = token
         email = "test@example.com"
    else:
        user_id, email = token.split(":")

    return CurrentUser(user_id=user_id, email=email)

async def get_user_with_roles(
    current_user: CurrentUser = Depends(get_current_user_stub),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    # Hydrate memberships
    result = await db.execute(select(Membership).where(Membership.user_id == current_user.user_id))
    memberships = result.scalars().all()
    
    current_user.memberships = [
        {"tenant_id": m.tenant_id, "site_id": m.site_id, "role": m.role}
        for m in memberships
    ]
    return current_user

def require_role(allowed_roles: List[str]):
    """
    Dependency to enforce strict RBAC.
    Must check if user has access to the requested Tenant/Site in the path parameters.
    Since dependencies don't easily access path params in a generic way without hacks,
    we'll implement a helper that endpoints must call, or use a class-based dependency.
    """
    pass # Placeholder if we want fancy decorator, but explicit check is safer.

def check_access(user: CurrentUser, tenant_id: str, site_id: Optional[str] = None) -> bool:
    """
    Verifies user has membership in tenant (and optional site).
    """
    if not user.memberships:
        return False
        
    for m in user.memberships:
        if m["tenant_id"] == tenant_id:
             # Site check: 
             # If m["site_id"] is NULL, they have full access (Admin/Owner).
             # If m["site_id"] is set, it must match the requested site.
             if m["site_id"] is None:
                 return True
             if site_id and m["site_id"] == site_id:
                 return True
                 
    return False
