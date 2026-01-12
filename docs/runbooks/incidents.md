# SIMCO AI Incident Response Playbooks (v3.1)

Actionable guides for fleet-scale operational issues.

## 🚨 Incident 1: Device Offline Spike
**Symptoms**: `edge.uplink.last_success_ts` aging out across multiple sites.
**Metrics**: `edge.uplink.failure_count` increasing; `cloud.ingest.accepted_count` dropping.
**Actions**:
1. Check Cloud ISP / Regional GCP health.
2. Verify Edge Token rotation state (log audit events for `ENROLLMENT_FAILED`).
3. Mitigate: If localized, restart site-gateway container.

## 🚨 Incident 2: Buffer Depth Growing
**Symptoms**: `edge.buffer.queued_count` > 5,000; `oldest_age` > 1 hour.
**Metrics**: `edge.uplink.success_count` is low relative to `edge.driver.poll.duration_ms`.
**Actions**:
1. Check UplinkWorker logs for `Backing off`.
2. check Cloud Ingestion Latency (`cloud.ingest.latency_ms`).
3. Mitigate: Increase `UPLOAD_BATCH_SIZE` temporarily; Increase `UPLOAD_INTERVAL_SECONDS` if cloud is throttling.

## 🚨 Incident 3: Notification Failure / Alert Storm
**Symptoms**: Customer complains of missing alerts or 100+ duplicate emails.
**Metrics**: `cloud.notifications.failed_count` spiking; `cloud.processor.events_emitted_count` high.
**Actions**:
1. Check NotificationDispatcher `rate_limits` state.
2. Verify Webhook endpoint status (look for 5xx in notify logs).
3. Mitigate: Flush `StreamProcessor` state; Enable "Global Mute" in cloud config if storming.

## Escalation Path
- **Level 1 (NOC)**: Triage via Fleet Health View.
- **Level 2 (SRE)**: Logic/Scaling issues.
- **Level 3 (Dev)**: Contract/Schema/Protocol issues.
