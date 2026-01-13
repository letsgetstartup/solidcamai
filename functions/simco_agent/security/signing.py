import os
import logging
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

logger = logging.getLogger("simco_agent.security.signing")

class SignatureVerifier:
    """Verifies Ed25519 signatures for artifact integrity."""

    def __init__(self, public_key_path: str):
        self.public_key_path = public_key_path
        self._public_key = None

    def _load_key(self):
        if self._public_key:
            return
        
        if not os.path.exists(self.public_key_path):
            raise FileNotFoundError(f"Verification public key not found: {self.public_key_path}")
            
        with open(self.public_key_path, "rb") as f:
            key_bytes = f.read()
            self._public_key = ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)

    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """Verifies an Ed25519 signature against data."""
        try:
            self._load_key()
            self._public_key.verify(signature, data)
            return True
        except InvalidSignature:
            logger.error("Invalid artifact signature detected!")
            return False
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

def verify_driver_artifact(zip_path: str, sig_path: str, pubkey_path: str) -> bool:
    """Helper to verify a driver zip file against its signature."""
    if not os.path.exists(zip_path) or not os.path.exists(sig_path):
        logger.error(f"Missing artifact or signature file: {zip_path}, {sig_path}")
        return False
        
    with open(zip_path, "rb") as f:
        data = f.read()
    with open(sig_path, "rb") as f:
        sig = f.read()
        
    verifier = SignatureVerifier(pubkey_path)
    return verifier.verify_signature(data, sig)
