from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
import os
import logging

logger = logging.getLogger(__name__)

class IdentityManager:
    """
    Manages the Gateway's identity (Private Key + Certificate).
    """
    def __init__(self, pki_dir="/etc/simco/pki"):
        self.pki_dir = pki_dir
        self.key_path = os.path.join(pki_dir, "device.key")
        self.cert_path = os.path.join(pki_dir, "device.crt")
        os.makedirs(pki_dir, exist_ok=True)

    def ensure_key(self) -> rsa.RSAPrivateKey:
        if os.path.exists(self.key_path):
             with open(self.key_path, "rb") as f:
                 return serialization.load_pem_private_key(f.read(), password=None)
        
        logger.info("Generating new Device Key...")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        with open(self.key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        return key

    def generate_csr(self, gateway_id: str) -> str:
        key = self.ensure_key()
        
        csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"gateway:{gateway_id}"),
        ])).sign(key, hashes.SHA256())
        
        return csr.public_bytes(serialization.Encoding.PEM).decode()

    def store_cert(self, cert_pem: str):
        with open(self.cert_path, "w") as f:
            f.write(cert_pem)
        logger.info(f"Stored device certificate at {self.cert_path}")

identity_manager = IdentityManager(pki_dir="./dev_certs") # Default to local dev dir
