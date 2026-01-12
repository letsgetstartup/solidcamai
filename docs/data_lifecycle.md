# SIMCO AI Data Lifecycle Policy (v3.1)

Managing industrial telemetry at scale with cost efficiency and compliance.

## 1. Storage Architecture
- **Operational Store (Hot Path)**: Transient state for rule evaluation and real-time dashboarding.
- **Data Warehouse (Cold Path)**: BigQuery for historical analysis, long-term trends, and auditability.
- **Archive Store (Coldest Path)**: GCS for data older than retention limits, stored in compressed Parquet format.

## 2. Retention Plans
| Plan | Raw Telemetry | Hourly Rollups | Daily Rollups | Events/Alerts |
|------|---------------|----------------|---------------|---------------|
| `pilot` | 30 Days | 180 Days | 2 Years | 180 Days |
| `standard` | 90 Days | 1 Year | 3 Years | 1 Year |
| `enterprise` | 180 Days | 2 Years | 5 Years | 2 Years |

## 3. Deletion Workflow (Compliance)
1. **Request**: Tenant administrator initiates a deletion request via Portal API.
2. **Review**: Automated dry-run generates a "Blast Radius" report (affected partitions/rows).
3. **Approval**: Request is moved to `deletion_requests` collection.
4. **Execution**: `process_deletions.py` identifies and removes the scoped data.
5. **Audit**: AUDIT event is emitted with the requester's ID and original scope.

## 4. Archiving Behavior
- Data is moved to GCS before BigQuery partition expiration.
- Archive paths: `gs://[BUCKET]/[TENANT]/[SITE]/[YYYY]/[MM]/[DD]/batch.parquet`
