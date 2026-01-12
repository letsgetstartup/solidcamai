# Customer IT Checklist: Infrastructure Requirements

This document is for Customer IT departments to prepare the network for SIMCO AI.

## Firewall Policy (Outbound)
| Destination | Port | Purpose |
| :--- | :--- | :--- |
| `*.cloudfunctions.net` | 443 | Telemetry Ingest & MGMT |
| `*.googleapis.com` | 443 | BigQuery & Storage |
| `*.docker.com` | 443 | Image Registry (if Docker used) |

## OT Network Access
- Gateway requires IP reachability to CNC machine IPs.
- **Protocol**: MTConnect (HTTP/XML) or FOCAS (TCP).
- **Discovery**: ICMP Ping or Port 80/5002 scanning allowed?

## Resource Requirements
- **RAM**: 512MB Minimum.
- **CPU**: 1 Core (ARM64/x86_64).
- **Disk**: 4GB SLC/pSLC recommended (SQLite persistence).
