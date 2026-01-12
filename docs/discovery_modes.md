# Discovery Modes & Policy Engine

The SIMCO AI Agent supports multi-mode machine discovery to balance speed, coverage, and network safety.

## Discovery Modes

### 1. Passive Discovery
- **Behavior**: Parses the system ARP table (`ip neigh`) and DHCP leases.
- **Safety**: Zero packets sent to scanning targets. Perfect for "no-scan" industrial zones.
- **Confidence**: Medium (Indicates device presence, but not protocol readiness).

### 2. Active Discovery
- **Behavior**: Performs rate-limited TCP port probes on specified subnets.
- **Safety**: Strict Packets-Per-Second (PPS) limits and subnet allowlists.
- **Confidence**: High (Confirms protocol availability).

### 3. Hybrid Discovery (Default)
- **Behavior**: Runs passive discovery first to find candidates, then performs targeted active probes only on discovered or missing ranges.

### 4. Manual Only
- **Behavior**: All automated scanning is disabled. Machines are only onboarded via the Manual Enrollment workflow.

## Discovery Policy Configuration

Controlled via Cloud Site Configuration:

```yaml
discovery_policy:
  mode: "hybrid" # active | passive | hybrid | manual_only
  active_enabled: true
  active_rate_limit_pps: 10
  allowed_subnets: ["192.168.1.0/24"]
  port_probes: [8193, 502, 44818]
```

## Manual Enrollment Workflow

1. **Portal**: Admin navigates to Site -> "Add Machine (Manual)".
2. **Cloud API**: `POST /v1/tenants/{t}/sites/{s}/machines:manual_enroll` is called.
3. **Edge Cloud Sync**: The agent's `ConfigManager` receives the new entry in the next config delta.
4. **Agent Action**: The entry is atomically added to `machine_registry.json`, and drivers are launched.
