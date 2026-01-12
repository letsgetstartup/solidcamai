# SIMCO AI Service Level Objectives (SLOs)

Target performance and reliability metrics for GA readiness.

## 1. Freshness SLO (Availability)
- **Objective**: 99.9% of devices have `last_seen` <= 2 minutes.
- **Goal**: Detect offline machines in near real-time.

## 2. Ingest Latency SLO
- **Objective**: p95 ingestion latency < 500ms.
- **Goal**: Ensure edge buffers drain quickly.

## 3. Hot-Path Alerting SLO
- **Objective**: 99% of ANOMALY events dispatched within 5 seconds of telemetry ingestion.
- **Goal**: Sub-second industrial response.

## 4. Data Loss SLO (Durability)
- **Objective**: 0 records dropped due to buffer overflow or unauthorized rejection of valid tokens.
- **Goal**: 100% auditability.

## 5. Portal API SLO
- **Objective**: 99% of read requests < 300ms.
- **Goal**: Snappy UI experience.
