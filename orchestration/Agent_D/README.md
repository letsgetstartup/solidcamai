# Agent D: Data Architect (Cloud Intelligence Custodian)

## 🎯 Overview & Mission
Agent D is the **Data Governance Master** of the SIMCO AI Cloud. It manages the BigQuery information lifecycle, ensuring that multi-terabyte shop floor data remains queryable, cost-effective, and architecturally sound.

## 🏗️ Technical Architecture
### Deployment & Stack
- **Platform**: Google BigQuery (Data Warehouse).
- **Core Strategy**: **Time-series Partitioning** and **ID-based Clustering**.
- **Transformation**: Materialized views for "Real-time" dashboard acceleration.

### Data Flow
1. **Ingest**: Receives data via Serverless Cloud Functions (Agent C).
2. **Partition**: Automatically buckets data into **Daily Partitions** using the `TIMESTAMP` column.
3. **Archive**: Moves data to Long-term storage (Cold) after 90 days.

## 🚀 Production Best Practices
- **Cost Optimization**: **Clustering** by `machine_id` to allow "Block Pruning", reducing query costs by up to 90% for specific machine lookups.
- **Query Guardrails**: Enforced partition filters on all dashboard queries to prevent expensive full-table scans.
- **Materialization**: Uses Materialized Views for KPI aggregation (OEE, Spindle Load) to reduce repetitive compute costs.

## 🛡️ Security & Compliance
- **Access Control**: Identity-Bound IAM policies. Dashboard service accounts only have `Data Viewer` rights to specific views.
- **Retention**: Configured with a 7-year retention policy to meet industrial certification requirements.
- **Data Sovereignty**: Enforced multi-regional storage to satisfy client privacy agreements.

## 🔄 Orchestration & Lifecycle
- **Input**: Ingestion stream from Cloud Functions.
- **Consumer**: Agent F (Interaction Manager) and Agent G (Audit).
- **Interface**: BigQuery SQL (Standard SQL).
- **Failure Recovery**: Point-in-time recovery (PITR) enabled via BigQuery snapshots.

## 📊 Observability (SLIs)
- **Query Cost-per-Report**: Average GCP cost for dashboard refreshes.
- **Data Freshness**: Latency between `ingest_timestamp` and view availability.
- **Schema Drift**: Number of rejected/failed ingestion rows due to format mismatch.

## 🏁 Operational Status
- **Current Status**: 🟢 **OPERATIONAL**
- **Last Sync**: BigQuery schema version 2.1.0 synchronized.
- **Next Job Execution**: Partition Optimization & Materialized View Refresh at **00:00 UTC**.
