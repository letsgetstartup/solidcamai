import hmac
import hashlib
import base64
import json
import time
import os
import logging

logger = logging.getLogger(__name__)

# Secret for signing Gateway Tokens (HS256)
# In PROD: Securely inject this via Google Secret Manager
JWT_SECRET = os.environ.get("JWT_SECRET", "dev_secret_change_me_in_prod")

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_gateway_token(gateway_id: str, tenant_id: str, site_id: str, expiry_seconds: int = 3600 * 24 * 30) -> str:
    """
    Creates a long-lived JWT for an Edge Gateway.
    Default expiry: 30 days.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "uid": gateway_id, # Reusing 'uid' claim for identity
        "sub": gateway_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "role": "gateway", # Explicit role
        "iat": int(time.time()),
        "exp": int(time.time()) + expiry_seconds
    }
    
    encoded_header = base64url_encode(json.dumps(header).encode('utf-8'))
    encoded_payload = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    signature = hmac.new(
        JWT_SECRET.encode('utf-8'),
        f"{encoded_header}.{encoded_payload}".encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    encoded_signature = base64url_encode(signature)
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def verify_gateway_token(token: str) -> dict:
    """
    Verifies a Gateway JWT.
    Returns payload dict if valid, Raises Exception if invalid.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid Token Format")
            
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify Signature
        expected_signature = hmac.new(
            JWT_SECRET.encode('utf-8'),
            f"{header_b64}.{payload_b64}".encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        if base64url_encode(expected_signature) != signature_b64:
            raise ValueError("Invalid Signature")
            
        # Decode and Check Expiry
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        
        if payload.get("exp") and payload["exp"] < time.time():
            raise ValueError("Token Expired")
            
        return payload
        
    except Exception as e:
        logger.warning(f"Gateway Token Verification Failed: {e}")
        raise e
