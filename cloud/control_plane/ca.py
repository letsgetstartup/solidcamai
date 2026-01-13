from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.x509.oid import NameOID
import datetime
import uuid
import os

class SimpleCA:
    def __init__(self, ca_cert_path="ca.crt", ca_key_path="ca.key"):
        self.ca_cert_path = ca_cert_path
        self.ca_key_path = ca_key_path
        self._load_or_generate_ca()

    def _load_or_generate_ca(self):
        if os.path.exists(self.ca_cert_path) and os.path.exists(self.ca_key_path):
            with open(self.ca_cert_path, "rb") as f:
                self.ca_cert = x509.load_pem_x509_certificate(f.read())
            with open(self.ca_key_path, "rb") as f:
                self.ca_key = serialization.load_pem_private_key(f.read(), password=None)
        else:
            self._generate_ca()

    def _generate_ca(self):
        # Generate Key
        self.ca_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )
        
        # Self-sign Cert
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"SIMCO Root CA"),
        ])
        
        self.ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            subject
        ).public_key(
            self.ca_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=3650)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True,
        ).sign(self.ca_key, hashes.SHA256())
        
        # Determine paths (handle test env where paths might be read-only if not careful, but usually ok)
        # For Cloud Run, secrets are mounted; for this MVP, we write to ./
        
        with open(self.ca_key_path, "wb") as f:
            f.write(self.ca_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=NoEncryption()
            ))

        with open(self.ca_cert_path, "wb") as f:
            f.write(self.ca_cert.public_bytes(Encoding.PEM))

    def sign_csr(self, csr_pem: bytes, subject_name: str) -> bytes:
        csr = x509.load_pem_x509_csr(csr_pem)
        
        # Enforce Subject (ignore CSR subject, set our own based on Gateway ID)
        new_subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"SIMCO AI"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            new_subject
        ).issuer_name(
            self.ca_cert.subject
        ).public_key(
            csr.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=90) # 90 day rotation policy
        ).add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True,
        ).sign(self.ca_key, hashes.SHA256())
        
        return cert.public_bytes(Encoding.PEM)

# Global CA Instance
ca_service = SimpleCA()
