# Security & Compliance Architecture

SIMCO AI implements the Siemens Level v3.1 security baseline for industrial IoT.

## 🛡️ Device Identity (mTLS)
- **Model**: Mutual TLS (X.509) for all Edge-to-Cloud communication.
- **Identity**: Every agent has a unique certificate/key pair bound to its hardware fingerprint.
- **Revocation**: Certificates can be revoked at the cloud gateway without affecting other devices.

## 🔐 Artifact Integrity (Signed Updates)
- **Scheme**: Ed25519 digital signatures.
- **Policy**: "Fail-Closed". The agent will NOT activate any driver or software update unless the signature verification matches the pinned public key.
- **Verification**: SHA-256 for corruption, Ed25519 for authenticity.

## 📋 Compliance Gates
- **SBOM**: Software Bill of Materials generated in CycloneDX format for every release.
- **Vulnerability Scanning**: CI/CD pipeline runs `pip-audit` on every commit.
- **Static Analysis**: `bandit` is used to detect security anti-patterns in Python code.

## 📜 Audit Logging
- **Scope**: All privileged actions (enrollment, config changes, health alerts).
- **Structure**: Actor, Action, Timestamp, and Before/After state.
- **Immutability**: Logs are streamed to a dedicated audit store (Firestore) for non-repudiation.

## 🚀 How to Run Security Checks
```bash
# Install tools
pip install -r requirements-dev.txt

# Run automated scan
bash scripts/security_checks.sh
```
