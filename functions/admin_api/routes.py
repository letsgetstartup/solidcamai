import logging
import json
from firebase_admin import auth
from firebase_functions import https_fn
from google.cloud import bigquery
from auth.claims import set_custom_claims

logger = logging.getLogger(__name__)

def dispatch(req: https_fn.Request) -> https_fn.Response:
    """
    Dispatcher for /admin_api/v1/...
    Protected by @require_auth in main.py.
    """
    path = req.path
    method = req.method
    claims = getattr(req, 'claims', None)

    # Hard RBAC: Only 'admin' role can access this API
    if not claims or claims.role != 'admin':
        return https_fn.Response(json.dumps({"error": "Forbidden", "message": "Admin Access Required"}), status=403, mimetype="application/json")

    # Routes
    if path.endswith("/invites") and method == "POST":
        return create_invite(req, claims)
    
    if path.endswith("/tenants") and method == "POST":
        return create_tenant(req, claims)

    return https_fn.Response(json.dumps({"error": "Not Found"}), status=404, mimetype="application/json")

def create_invite(req: https_fn.Request, admin_claims: object) -> https_fn.Response:
    """
    Invites a user to the platform by creating their account and setting claims.
    """
    data = req.get_json(silent=True) or {}
    email = data.get('email')
    role = data.get('role', 'viewer')
    target_site = data.get('site_id') # Optional
    
    if not email:
        return https_fn.Response(json.dumps({"error": "Missing Email"}), status=400, mimetype="application/json")

    # Tenant Scoping: Admins can only invite to their own tenant
    # (Super-admins for cross-tenant creation not implemented in this logic yet, assuming tenant-admin)
    target_tenant = admin_claims.tenant_id

    try:
        # Check if user exists
        try:
            user = auth.get_user_by_email(email)
            uid = user.uid
            created = False
        except auth.UserNotFoundError:
            # Create new user
            user = auth.create_user(email=email, email_verified=False)
            uid = user.uid
            created = True

        # Set Claims
        set_custom_claims(uid, target_tenant, target_site, role)

        return https_fn.Response(json.dumps({
            "message": "User Invite Processed",
            "uid": uid,
            "created": created,
            "claims": {"tenant_id": target_tenant, "site_id": target_site, "role": role}
        }), status=200, mimetype="application/json")

    except Exception as e:
        logger.error(f"Invite Error: {e}")
        return https_fn.Response(json.dumps({"error": str(e)}), status=500, mimetype="application/json")

def create_tenant(req: https_fn.Request, admin_claims: object) -> https_fn.Response:
    """
    Creates a new Tenant record.
    Realistically, only a 'Global Admin' (Simco Staff) should do this.
    For now, we allow any admin to 'register' sub-entities or we rely on a specific Global Tenant ID.
    PROD: Check if admin_claims.tenant_id == 'simco_global'
    """
    # ... Implementation pending BigQuery Schema update for Tenants table ...
    return https_fn.Response(json.dumps({"message": "Tenant creation stub"}), status=501, mimetype="application/json")
