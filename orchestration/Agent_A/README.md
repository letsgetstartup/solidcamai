# Agent A: DevOps & Recon (Industrial Discovery Orchestrator)

## 🎯 Overview & Mission
Agent A acts as the **top-level orchestrator** for local environment discovery. Its mission is to maintain a real-time, high-fidelity digital twin of the physical machine shop topology, ensuring zero-touch onboarding for CNC assets.

## 🏗️ Technical Architecture
### Deployment & Stack
- **Runtime**: Python 3.11+ / Dockerized Edge Container.
- **Scanning Library**: `python-nmap` (Low-level TCP/IP stack interaction).
- **Core Strategy**: **Infrastructure as Code (IaC)**. The registry is treated as the "Source of Truth" for the entire edge ecosystem.

### Data Flow
1. **Sweep**: Passive & active network discovery.
2. **Identification**: Fingerprinting machine controllers (Fanuc, Heidenhain, Siemens).
3. **Registration**: Updating `machine_registry.json` with mDNS/IP metadata.

## 🚀 Production Best Practices
- **Scanning Intervals**: Optimized 300s deep-scans with 30s "heartbeat" pings to minimize network overhead on industrial switchgear.
- **Concurrency**: Asynchronous scanning to prevent blocking edge resources.
- **Registry Versioning**: Atomic writes to the registry file to prevent corruption during power loss.

## 🛡️ Security & Compliance
- **Scan Isolation**: Logic Restricted to designated industrial VLANs.
- **Identity**: Uses mTLS to authenticate its "Registry Update" requests.
- **Governance**: Maintains an audit log of all newly discovered assets for IT department reconciliation.

## 🔄 Orchestration & Lifecycle
- **Trigger**: System boot-up followed by cron-based periodic execution.
- **Downstream Consumers**: 
  - **Agent B (Ingestor)**: Subscribes to registry changes to start/stop polling threads.
  - **Agent G (QA)**: Audits the registry for stale or zombie machine entries.
- **Failure Recovery**: Automatic retry logic with exponential backoff on `nmap` execution failures.

## 📊 Observability (SLIs)
- **Discovery Accuracy**: % of correctly identified controller types.
- **Scan Latency**: Time to complete a full shop-floor sweep.
- **Asset Drift**: Number of rogue devices detected vs. authorized registry.

## 🏁 Operational Status
- **Current Status**: 🟢 **OPERATIONAL**
- **Last Sync**: Registry updated successfully.
- **Next Job Execution**: Industrial Network Discovery Sweep in **300.0s**.
