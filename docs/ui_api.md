# SIMCO AI UI API Spec (v1)

All endpoints return data from the **Operational Hot Path** (Latest State + Events).

## Endpoints

### List Sites
`GET /v1/tenants/{tenant_id}/sites`
- **RBAC**: Manager, Installer, Operator, Maintenance (Scoped to tenant)
- **Returns**: `[{"site_id": "...", "name": "...", "machine_count": 0}, ...]`

### List Machines
`GET /v1/tenants/{tenant_id}/sites/{site_id}/machines`
- **RBAC**: Manager, Installer, Operator, Maintenance (Scoped to site)
- **Returns**: `[{"machine_id": "...", "status": "ONLINE", "last_seen": "..."}, ...]`

### Get Machine State
`GET /v1/tenants/{tenant_id}/sites/{site_id}/machines/{machine_id}/state`
- **RBAC**: Manager, Operator, Maintenance
- **Returns**: Full `TelemetryRecord` (latest)

### Get Machine Events
`GET /v1/tenants/{tenant_id}/sites/{site_id}/events?machine_id=...&since=...`
- **RBAC**: Manager, Operator, Maintenance
- **Returns**: `[{"event_id": "...", "type": "...", "severity": "...", "timestamp": "..."}, ...]`
