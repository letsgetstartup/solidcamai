# Big Screen Wallboard (85" Entrance Screen)

The Big Screen Wallboard is a read-only, always-on UI designed for large-format displays in CNC shops. It provides real-time visibility into fleet status, alerts, and production progress.

## Features
- Real-time fleet status (Running, Idle, Alarm, Offline).
- Live machine tiles with key metrics (Spindle Load, Feed Rate).
- Active alerts sorted by severity.
- ERP Production orders integration (requires `SIMCO_BIGSCREEN_ERP_ENABLED=1`).
- Secure "Display Device Token" authentication (no human login required).
- Stale data detection and offline resilience.

## Setup Instructions

### 1. Generate a Display Token
In the Management Portal (or directly via the Control Plane API), create a new Display Device.
```bash
curl -X POST http://localhost:8080/displays \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant_demo", "site_id": "site_demo", "name": "Main Entrance"}'
```
This will return a `token`. Copy this token.

### 2. Configure the Wallboard Link
The wallboard URL format is:
`http://<PODTRAL_URL>/bigscreen.html?tenant=<TID>&site=<SID>&display_token=<TOKEN>`

Example:
`http://localhost:5173/bigscreen.html?tenant=tenant_demo&site=site_demo&display_token=SECRET_TOKEN`

### 3. Kiosk Mode Mounting
It is recommended to run the wallboard browser in "Kiosk Mode" on the target hardware.
Example for Chrome:
`google-chrome --kiosk "URL_HERE"`

## Technical details
- **Poll Interval**: 3 seconds.
- **Backend Endpoint**: `GET /portal_api/v1/tenants/{tid}/sites/{sid}/bigscreen/summary`.
- **Data Refresh**: 
  - Telemetry: Hot-path (in-memory processor state).
  - ERP: BigQuery view (cached for 30s server-side).

## Troubleshooting
- **STALE Banner**: Indicates the backend hasn't received telemetry data for over 60 seconds.
- **OFFLINE / ERROR**: Indicates connectivity issues between the wallboard and the Portal API.
