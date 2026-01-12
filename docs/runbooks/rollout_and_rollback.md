# Rollout & Rollback Playbook

## 1. Deployment Rings
- **Ring 0 (Dev)**: Internal R&D Lab.
- **Ring 1 (Staging)**: Selected pilot sites (Canary).
- **Ring 2 (Production)**: Global fleet.

## 2. Canary Targeting
- Target by `tenant_id` or `site_tags` in the Management Plane.
- Enrollment of new versions should be staggered (10% -> 50% -> 100%).

## 3. Rollback Triggers
Rollback MUST be initiated if:
- **CrashLoop**: Agent restarts > 5 times in 10 minutes.
- **Error Spike**: Telemetry drop > 20% compared to baseline.
- **Watchdog Timeout**: Ingestor stops processing records.
- **Security Breach**: Invalid mTLS handshake detected.

## 4. Rollback Procedures
### Runtime Rollback
- **Docker**: `docker stop ...`, `docker run <previous_tag>`.
- **systemd**: `bash deploy/systemd/rollback.sh` (or revert /opt/ links).

### Driver Rollback
- Rename `drivers_active` to `drivers_failed`.
- Restore `drivers_backup` to `drivers_active`.
- Restart Agent.
