# SIMCO AI Acceptance Gates (v3.1)

This document defines the formal engineering gates required for Pilot Qualification and Client Acceptance.

| Gate ID | Requirement | Threshold | Measurement Method | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **DISCO_01** | Discovery Coverage | >= 95% of hosts found | Pilot Suite (Subnet Scan) | Agent A |
| **DISCO_02** | Discovery Speed | <= 5 minutes for /24 | Pilot Suite (Timer) | Agent A |
| **DUR_01** | Outage Resilience | 0% Data Loss | Pilot Suite (Outage Sim) | Agent B |
| **DUR_02** | Backfill Rate | Queue → 0 after recovery | Pilot Suite (Queue Poll) | Agent B |
| **DATA_01** | Schema Compliance | 100% Pydantic Valid | Pilot Suite (Ingest Stub) | Agent C |
| **ID_01** | Identity Stability | Multi-run consistency | Pilot Suite (UUID Check) | Agent G |
| **SEC_01** | mTLS Enforcement | 100% reject no-cert | Pilot Suite (Handshake) | Agent E |
| **SEC_02** | Signed Artifacts | 100% reject unsigned | Pilot Suite (Update Sim) | Agent E |

## Certification Process
1. **Runner**: `scripts/pilot/run_pilot_suite.py`
2. **Evaluator**: `simco_agent/core/qa_certify.py`
3. **Artifact**: `CLIENT_ACCEPTANCE_CERTIFICATE.md`
