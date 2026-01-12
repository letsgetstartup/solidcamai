# Installer Checklist: SIMCO AI Edge Gateway

This checklist is for field engineers performing the physical and initial logical setup of the gateway.

## Pre-Installation
- [ ] Verify Power Supply (12-24V DC / AC Adapter).
- [ ] Verify OT Ethernet connectivity to CNC subnet.
- [ ] Verify WAN connectivity (WiFi/SIM/Industrial VPN).

## Physical Installation
- [ ] Mount hardware (DIN Rail / Wall Mount).
- [ ] Connect Power + Ethernet.
- [ ] Verify Link LED on NIC.

## Logical Setup
- [ ] Boot device.
- [ ] Run enrollment: `python -m simco_agent.core.provisioning`.
- [ ] Verify `device_state.json` is generated.
- [ ] Confirm Heartbeat is blue/green in Cloud Portal.

## Validation
- [ ] Run discovery: `python -m simco_agent.core.sync_manager` (manual trigger).
- [ ] Check `machine_registry.json` for discovered hosts.
- [ ] **Target Time-to-Install**: < 15 minutes.
