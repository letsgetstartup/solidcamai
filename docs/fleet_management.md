# Fleet Management & Lifecycle

The SIMCO AI Agent includes a comprehensive Management Plane for secure enrollment, remote configuration, and fleet-wide health monitoring.

## Enrollment (Zero-Touch)
1. **Bootstrap**: New agents start with a short-lived `SIMCO_BOOTSTRAP_TOKEN`.
2. **Identification**: The agent sends a device fingerprint (hostname, MAC, software version).
3. **Binding**: The Cloud Management Plane returns a permanent `device_id` and binds the agent to a `tenant_id` and `site_id`.
4. **Persistence**: Identity is stored atomically in `device_state.json`.

## Configuration Management
- **Polling**: Agents poll the `/get_config` endpoint every 60s.
- **Versioning**: Configuration is versioned on the cloud. Agents only apply updates when the version increments.
- **Deltas**: The cloud provides full or partial configuration deltas.
- **Audit**: Every configuration change emits a `CONFIG_CHANGED` event to the telemetry pipeline.

## Fleet Health (Heartbeat)
Agents report their health every 30s via the `/heartbeat` endpoint:
- **Runtime Version**: Current agent software version.
- **Buffer Depth**: Number of telemetry records currently queued in SQLite.
- **Disk Usage**: Available space on the local drive.
- **Machine Count**: Number of industrial machines currently monitored.
- **Connectivity**: Last successful upload timestamp.
