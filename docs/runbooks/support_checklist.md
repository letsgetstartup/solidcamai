# Support Checklist: SIMCO AI Edge Gateway

This checklist is for Level 1/2 Support Engineers troubleshooting field issues.

## 1. Quick Health Check
- [ ] **Last Seen**: Check Cloud Portal machine list.
- [ ] **Buffer Depth**: Is `buffer.db` growing? (Check `stats()`).
- [ ] **Disk Usage**: Ensure >1GB free.

## 2. Common Issues
| Symptom | Action |
| :--- | :--- |
| **No Telemetry** | Check `machine_registry.json`. Is discovery running? |
| **Buffer Overflow** | Check `INGEST_URL` reachability. Run `ping` to cloud. |
| **Auth Failures** | Verify `DEVICE_CERT_PATH`. Check enrollment status. |

## 3. Support Bundle
- Run `python -m simco_agent.tools.support_bundle --out ./bundle.zip`.
- Send bundle.zip to R&D for analysis.

## 4. Escalation
- If issue persists after driver restart, escalate to Agent F (AI Investigator).
