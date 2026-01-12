# Agent G: QA & Acceptance (Autonomous Systems Auditor)

## 🎯 Overview & Mission
Agent G is the **Final Authority** on system health. It provides autonomous self-certification for the entire 7-agent loop, ensuring that every component is meeting its Service Level Objectives (SLOs) and generating official Client Acceptance Certificates.

## 🏗️ Technical Architecture
### Deployment & Stack
- **Runtime**: Hybrid (Local Edge Auditor + Cloud Audit Function).
- **Core Logic**: Logic gates based on the health status of Agents A through F.
- **Reporting**: Automated Markdown/PDF generation for system certification.

### Data Flow
1. **Audit**: Queries SLI metrics from all other agents.
2. **Evaluate**: Compares real-time performance against predefined SLO thresholds.
3. **Certify**: Generates a timestamped, signed `CLIENT_ACCEPTANCE_CERTIFICATE.md`.

## 🚀 Production Best Practices
- **Observability**: Implements the "Golden Signals" of monitoring: Latency, Traffic, Errors, and Saturation.
- **Self-Correction**: (Future) Capability to restart local orchestration containers if Agent B or C hangs.
- **Audit Integrity**: The Audit Agent has "Read Only" access to logs but "Write" access to the Certificate store.

## 🛡️ Security & Compliance
- **Independent Verification**: Operates outside the standard telemetry pipeline to ensure unbiased reporting.
- **Tamper Evidence**: All certificates are hashed and logged to the Security Sentinel (Agent E).
- **Sovereignty**: Ensures that data handling certificates are generated for each individual machine shop tenant.

## 🔄 Orchestration & Lifecycle
- **Trigger**: Daily cron (00:00 UTC) or On-Demand via the Security Trigger function.
- **Output**: The [Client Acceptance Certificate](file:///Users/avirammizrahi/Desktop/solidcamai/simco-ai-v2/CLIENT_ACCEPTANCE_CERTIFICATE.md).
- **Authority**: If Agent G detects a critical failure, it flips the system status to "Maintenance Mode" in Agent F.

## 📊 Observability (SLIs)
- **Compliance Rate**: % of days with a valid "Green" certificate.
- **Audit Integrity**: Time between system failure and Agent G detection.
- **SLO Coverage**: Number of system parameters successfully monitored.

## 🏁 Operational Status
- **Current Status**: 🟢 **OPERATIONAL**
- **Last Sync**: Autonomous health audit verified 100% system readiness.
- **Next Job Execution**: Daily Client Acceptance Certificate Generation in **5.0m**.
