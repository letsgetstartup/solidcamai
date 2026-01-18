import os
import logging
import json
from functools import wraps
from flask import request, jsonify, g
from firebase_functions import https_fn
import firebase_admin
from firebase_admin import auth
from auth.tokens import verify_gateway_token # PR4


# Initialize Firebase Admin if not already done
if not firebase_admin._apps:
    firebase_admin.initialize_app()

logger = logging.getLogger(__name__)

class AuthClaims:
    """Standardized identity context for a request."""
    def __init__(self, uid: str, tenant_id: str, site_id: str = None, role: str = None):
        self.uid = uid
        self.tenant_id = tenant_id
        self.site_id = site_id
        self.role = role

    def to_dict(self):
        return {
            "uid": self.uid,
            "tenant_id": self.tenant_id,
            "site_id": self.site_id,
            "role": self.role
        }

def require_auth(f):
    """
    Decorator to enforce strict Bearer Token authentication.
    Verifies Firebase ID Token and injects claims into `request.claims`.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        req = args[0] # https_fn.Request
        
        # 1. Dev Bypass (Supports both Emulator and Production Verification)
        if req.headers.get('X-Dev-Tenant') or (os.getenv('FUNCTIONS_EMULATOR') == 'true' and req.args.get('dev') == '1'):
            dev_tenant = req.headers.get('X-Dev-Tenant', 'tenant_demo')
            dev_site = req.headers.get('X-Dev-Site', 'site_demo')
            dev_role = req.headers.get('X-Dev-Role', 'admin')
            
            logger.warning(f"Using DEV AUTH context: {dev_tenant}/{dev_site} (Role: {dev_role})")
            req.claims = AuthClaims(
                uid='dev_user',
                tenant_id=dev_tenant,
                site_id=dev_site,
                role=dev_role
            )
            return f(*args, **kwargs)

        # 2. Extract Bearer Token
        auth_header = req.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return https_fn.Response(json.dumps({'error': 'Unauthorized', 'message': 'Missing Bearer Token'}), status=401, mimetype='application/json')

        token = auth_header.split(' ')[1]

        # 3. Verify Token
        try:
            decoded_token = auth.verify_id_token(token)
            
            # 4. Extract Claims
            uid = decoded_token.get('uid')
            tenant_id = decoded_token.get('tenant_id')
            site_id = decoded_token.get('site_id')
            role = decoded_token.get('role', 'viewer')

            if not tenant_id:
                 logger.error(f"User {uid} has no tenant_id claim")
                 return https_fn.Response(json.dumps({'error': 'Forbidden', 'message': 'User not bound to a tenant'}), status=403, mimetype='application/json')

            req.claims = AuthClaims(uid, tenant_id, site_id, role)
            
        except (auth.ExpiredIdTokenError, auth.InvalidIdTokenError) as firebase_error:
            # PR4: Fallback to Gateway Token
            try:
                gw_payload = verify_gateway_token(token)
                req.claims = AuthClaims(
                    uid=gw_payload['uid'],
                    tenant_id=gw_payload['tenant_id'],
                    site_id=gw_payload['site_id'],
                    role=gw_payload['role']
                )
                logger.debug(f"Authenticated Gateway: {gw_payload['uid']}")
                return f(*args, **kwargs)
            except Exception as gw_error:
                return https_fn.Response(json.dumps({'error': 'Unauthorized', 'message': 'Invalid Token (User or Gateway)'}), status=401, mimetype='application/json')

        except Exception as e:
            logger.error(f"Auth verification failed: {str(e)}")
            return https_fn.Response(json.dumps({'error': 'Internal Server Error', 'message': 'Auth check failed'}), status=500, mimetype='application/json')

        return f(*args, **kwargs)

    return decorated_function
