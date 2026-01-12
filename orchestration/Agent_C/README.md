# Agent C: Cloud Uplink (Resilient Serverless Gateway)

## 🎯 Overview & Mission
Agent C is the **Mission-Critical Bridge** between the shop floor and Google Cloud. It ensures 100% data delivery resilience through advanced "Store-and-Forward" protocols and serves as the primary secure uplink for the Serverless transformation.

## 🏗️ Technical Architecture
### Deployment & Stack
- **Protocol**: HTTPS/2 with compression (Brotli/Gzip) for low-bandwidth cellular support.
- **Persistence**: SQLite-based local buffer for offline resilience.
- **Service**: Point-to-point connection to Firebase Cloud Functions.

### Data Flow
1. **Receive**: Accepts signed JSON packets from Agent B.
2. **Buffer**: Persists data to local NVMe storage if the uplink is down.
3. **Sync**: Expedites priority chunks (Alerts) while batching telemetry for efficiency.

## 🚀 Production Best Practices
- **Resilience**: **Exponential Backoff & Jitter** for connection retries to avoid "Thundering Herd" on server recovery.
- **Batching**: Payload aggregation (up to 500 records) to minimize HTTPS overhead and Cloud Function invocation costs.
- **Bandwidth Throttling**: Configurable uplink speed caps to prevent saturating industrial ISP pipelines.

## 🛡️ Security & Compliance
- **Identity**: Uses **Firebase Custom Tokens** (JWT) for individual device authentication.
- **Encryption**: TLS 1.3 for all data-in-transit.
- **Auditing**: Maintains a local "Sync Ledger" for forensic verification of cloud delivery.

## 🔄 Orchestration & Lifecycle
- **Input**: Telemetry Stream (Agent B).
- **Endpoint**: `https://[PROJECT].cloudfunctions.net/ingest_telemetry`.
- **Consumer**: Agent D (Data Architect) via the Serverless Ingestion layer.
- **Failure Recovery**: Multi-stage buffering. If local storage exceeds 1GB, Agent C triggers a "Data Pressure" alert to Agent G.

## 📊 Observability (SLIs)
- **Uplink Success Rate**: % of successfully delivered packets to Firebase.
- **Sync Lag**: Time difference between Edge capture and Cloud ingestion.
- **Buffer Depth**: Size of current local unsynced data queue.

## 🏁 Operational Status
- **Current Status**: 🟢 **OPERATIONAL**
- **Last Sync**: 104 packets synced to BigQuery via Serverless Ingest.
- **Next Job Execution**: Flush local SQLite buffer to BigQuery (Event-driven / 60s).
