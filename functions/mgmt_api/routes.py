import logging
import json
import uuid
import random
import string
import time
from firebase_functions import https_fn
from google.cloud import bigquery
from auth.tokens import create_gateway_token # PR4


# In-Memory Store for Pairing Codes (PROD: Use Firestore/Redis)
# Format: { "CODE123": {"tenant_id": "t1", "site_id": "s1", "expires_at": 1234567890} }
PAIRING_CODES_DB = {
    "999999": {"tenant_id": "tenant_demo", "site_id": "site_demo", "expires_at": 33256053890} # Persistent demo code
}

logger = logging.getLogger(__name__)

def dispatch(req: https_fn.Request) -> https_fn.Response:
    path = req.path
    method = req.method
    claims = getattr(req, 'claims', None)

    # 1. Pairing Code Generation (Admin Only)
    if path.endswith("/pairing_codes") and method == "POST":
        if not claims or claims.role != 'admin':
            return https_fn.Response("Forbidden", status=403)
        return generate_pairing_code(req, claims)

    # 2. Device Enrollment (Public/Unauthenticated start, or uses Code)
    if path.endswith("/enroll") and method == "POST":
        return enroll_device(req)

    # 3. Authenticated Device Endpoints (Require Gateway Identity - PR4)
    # For PR3, we assume they are open or check dev tokens lightly until PR4 enforces mTLS/JWT
    if path.endswith("/config") and method == "POST":
        return get_config(req)
        
    if path.endswith("/heartbeat") and method == "POST":
        return heartbeat(req)

    return https_fn.Response("Not Found", status=404)

def generate_pairing_code(req, admin_claims):
    """Generates a short-lived pairing code for a specific site."""
    data = req.get_json(silent=True) or {}
    site_id = data.get('site_id')
    tenant_id = admin_claims.tenant_id
    
    code = ''.join(random.choices(string.digits, k=6))
    PAIRING_CODES_DB[code] = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "expires_at": time.time() + 600 # 10 mins
    }
    
    logger.info(f"Generated Pairing Code {code} for {tenant_id}/{site_id}")
    return https_fn.Response(json.dumps({"code": code, "expires_in": 600}), mimetype="application/json")


def enroll_device(req):
    """Enrolls a device using a pairing code."""
    data = req.get_json(silent=True) or {}
    code = data.get("pairing_code")
    hw_info = data.get("hardware_info", {})
    
    record = PAIRING_CODES_DB.get(code)
    
    if not record:
        logger.warning(f"Invalid Pairing Code Attempt: {code}")
        return https_fn.Response(json.dumps({"error": "Invalid Code"}), status=403, mimetype="application/json")
        
    if record["expires_at"] < time.time():
        del PAIRING_CODES_DB[code]
        return https_fn.Response(json.dumps({"error": "Code Expired"}), status=403, mimetype="application/json")

    # Success
    device_id = str(uuid.uuid4())
    
    # PR4: Issue Signed JWT
    token = create_gateway_token(device_id, record['tenant_id'], record['site_id'])
    
    logger.info(f"Enrolled Device {device_id} for {record['tenant_id']} using code {code}")
    
    # Clean up code (One-time use)
    if code != "999999":
        del PAIRING_CODES_DB[code]
        
    return https_fn.Response(json.dumps({
        "device_id": device_id,
        "gateway_token": token, # PR4: Standard JWT
        "tenant_id": record["tenant_id"],
        "site_id": record["site_id"],
        "config": {"scan_interval": 30}
    }), mimetype="application/json")

def get_config(req):
    return https_fn.Response(json.dumps({
        "config_version": 2, 
        "changed": True, # Force update for testing
        "config": {
            "scan_interval": 60,
            "discovery": {
                "enabled": True,
                "subnets": ["192.168.1.0/24"], # Policy-driven subnet
                "protocols": ["opc_ua", "mtconnect", "focas"],
                "scan_interval_seconds": 300
            }
        }
    }), mimetype="application/json")

def heartbeat(req):
    return https_fn.Response(json.dumps({"status": "ok"}), mimetype="application/json")
