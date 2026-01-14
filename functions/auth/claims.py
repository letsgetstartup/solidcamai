import logging
import firebase_admin
from firebase_admin import auth

logger = logging.getLogger(__name__)

def set_custom_claims(uid: str, tenant_id: str, site_id: str = None, role: str = 'viewer'):
    """
    Sets custom claims on a Firebase User for multi-tenant RBAC.
    
    Args:
        uid: Firebase User ID
        tenant_id: The tenant this user belongs to.
        site_id: (Optional) Specific site scope. If None, user implies tenant-wide access (if role allows).
        role: Functional role (admin, manager, operator, viewer).
    """
    claims = {
        'tenant_id': tenant_id,
        'role': role
    }
    if site_id:
        claims['site_id'] = site_id
        
    try:
        auth.set_custom_user_claims(uid, claims)
        logger.info(f"Set claims for {uid}: {claims}")
        return True
    except Exception as e:
        logger.error(f"Failed to set claims for {uid}: {e}")
        raise e

def get_user_claims(uid: str):
    """Retrieves current custom claims for a user."""
    try:
        user = auth.get_user(uid)
        return user.custom_claims
    except Exception as e:
        logger.error(f"Failed to get user {uid}: {e}")
        return None
