# Role-Based Access Control (RBAC)

SIMCO AI enforces strict tenant-scoping and role-based permissions.

## Roles

| Role | Permissions |
| :--- | :--- |
| **Manager** | Full view of tenant sites, machines, and KPIs. |
| **Installer** | Device enrollment, discovery results, health monitoring. |
| **Operator** | Real-time status, event timelines, dashboard view. |
| **Maintenance** | Diagnostics, event history, error logs. |

## Enforcement
- **Tenant Scoping**: Users can only access data where `tenant_id` matches their context.
- **Site Scoping**: Some roles (e.g. Operator) may be further scoped to specific `site_id` values.
- **Validation**: Role and scope are validated server-side on every API request.
