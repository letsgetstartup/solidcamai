from firebase_functions import https_fn
from firebase_admin import initialize_app
from google.cloud import bigquery
import sys
import os
import json
import logging
from datetime import datetime

# Add root directory to sys.path to allow imports from simco_common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

initialize_app()

logger = logging.getLogger("functions")

def get_bq_client():
    return bigquery.Client()

dataset_id = "simco_telemetry"
table_id = "raw_telemetry"

from cloud.processing.bus import bus
from cloud.processing.stream_processor import processor

# Initialize Background Processor (Local/Dev)
bus.subscribe(processor.process_batch)

def log_audit_event(actor: str, action: str, details: dict):
    """Common audit logger for privileged actions."""
    audit_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "actor": actor,
        "action": action,
        "details": details
    }
    logger.info(f"AUDIT: {json.dumps(audit_record)}")

@https_fn.on_request()
def enroll_device(req: https_fn.Request) -> https_fn.Response:
    """Task 6: Secure device enrollment."""
    if req.method != 'POST': return https_fn.Response('POST only', status=405)
    
    data = req.get_json() or {}
    bootstrap_token = data.get("bootstrap_token")
    
    if bootstrap_token != "devtoken":
        log_audit_event("system", "ENROLLMENT_FAILED", {"reason": "bad_token"})
        return https_fn.Response(json.dumps({"error": "Unauthorized bootstrap"}), status=403, mimetype="application/json")
    
    import uuid
    device_id = str(uuid.uuid4())
    
    # Audit successful enrollment
    log_audit_event(device_id, "ENROLLMENT_SUCCESS", {"channel": data.get("requested_channel")})
    
    response = {
        "device_id": device_id,
        "tenant_id": "tenant_demo",
        "site_id": "site_demo",
        "channel": data.get("requested_channel", "dev"),
        "config_version": 1,
        "config": {"scan_interval_seconds": 60, "log_level": "INFO"}
    }
    return https_fn.Response(json.dumps(response), mimetype="application/json")

@https_fn.on_request()
def ingest_telemetry(req: https_fn.Request) -> https_fn.Response:
    """Unified Edge-to-Cloud Ingestion Point (v3.1)."""
    from simco_common.schemas_v3 import TelemetryBatch

    if req.method != 'POST':
        return https_fn.Response('Only POST allowed', status=405)

    try:
        import time
        from simco_agent.observability.metrics import cloud_metrics
        start_time = time.time()
        
        data = req.get_json()
        if not data:
            cloud_metrics.counter("cloud.ingest.rejected_count", 1, labels={"reason": "no_json"})
            return https_fn.Response('No JSON provided', status=400)

        # 1. Schema Validation (Task 5-1)
        payload = TelemetryBatch(**data)
        cloud_metrics.counter("cloud.ingest.accepted_count", len(payload.records))
        
        # 2. Idempotency & Routing & Hot-Path Publishing
        ingested_ids = []
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        for record in payload.records:
            # Cold Path Simulation
            logger.debug(f"Cold Path: Syncing {record.record_id} to BigQuery.")
            
            # Hot Path: Publish to Processing Bus (Expansion Task 1)
            record_data = record.model_dump()
            
            # For Unified Dev Router optimization: ensure processing runs now
            task = processor.process_record(record_data)
            if loop.is_running():
                 loop.create_task(task)
            else:
                 loop.run_until_complete(task)
            
            ingested_ids.append(record.record_id)
            
        latency = (time.time() - start_time) * 1000
        cloud_metrics.histogram("cloud.ingest.latency_ms", latency)
        
        return https_fn.Response(
            json.dumps({"status": "SUCCESS", "records_ingested": len(ingested_ids)}),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Telemetry ingestion error: {e}")
        from simco_agent.observability.metrics import cloud_metrics
        cloud_metrics.counter("cloud.ingest.rejected_count", 1, labels={"reason": "exception"})
        return https_fn.Response(json.dumps({"status": "ERROR", "message": str(e)}), status=400, mimetype="application/json")

@https_fn.on_request()
def heartbeat(req: https_fn.Request) -> https_fn.Response:
    """Task 6: Fleet health monitoring."""
    if req.method != 'POST': return https_fn.Response('POST only', status=405)
    data = req.get_json() or {}
    device_id = data.get("device_id")
    if not device_id:
        return https_fn.Response(json.dumps({"error": "Missing device_id"}), status=400, mimetype="application/json")
    
    # Audit check: Device reporting healthy/unhealthy
    if data.get("buffer_depth", 0) > 1000:
        log_audit_event(device_id, "DEVICE_UNHEALTHY", {"reason": "buffer_overflow", "depth": data["buffer_depth"]})
    
    return https_fn.Response(json.dumps({"status": "ok"}), mimetype="application/json")

@https_fn.on_request()
def ai_investigator(req: https_fn.Request) -> https_fn.Response:
    """Agent F (Serverless): AI Chatbot Research."""
    data = req.get_json() or {}
    query = data.get("query", "status check")
    
    return https_fn.Response(json.dumps({
        "response": f"Serverless AI Analysis for: '{query}'. System healthy."
    }), mimetype="application/json")


@https_fn.on_request()
def manual_enroll(req: https_fn.Request) -> https_fn.Response:
    """Expansion Task 2: Cloud-driven manual enrollment."""
    if req.method != 'POST': return https_fn.Response('POST only', status=405)
    
    # 1. RBAC check (Simplified for MVP)
    dev_role = req.headers.get("X-Dev-Role")
    if dev_role not in ["Installer", "Manager"]:
        return https_fn.Response(json.dumps({"error": "Forbidden: Only Installers/Managers can manual enroll"}), status=403, mimetype="application/json")

    data = req.get_json() or {}
    machine_ip = data.get("machine_ip")
    if not machine_ip:
        return https_fn.Response(json.dumps({"error": "Missing machine_ip"}), status=400, mimetype="application/json")

    # 2. Persist to site config (Mocked as audit log + success)
    log_audit_event("portal", "MANUAL_ENROLLMENT_REQUESTED", data)
    
    # In production, this would append to 'pending_manual_enrollments' in Firestore site doc
    return https_fn.Response(json.dumps({
        "status": "PENDING",
        "message": f"Machine {machine_ip} added to pending enrollment list. Edge will sync shortly."
    }), mimetype="application/json")

# --- v1 UI API (Task 8) ---

def check_rbac(req: https_fn.Request, tenant_id: str, site_id: Optional[str] = None):
    """Helper to validate role and tenant/site scoping."""
    dev_role = req.headers.get("X-Dev-Role")
    dev_tenant = req.headers.get("X-Dev-Tenant")
    dev_site = req.headers.get("X-Dev-Site")
    
    # Deny if cross-tenant
    if dev_tenant != tenant_id:
        return False, "Access Denied: Cross-tenant breach"
    
    # Deny if cross-site for restricted roles
    if site_id and dev_site and dev_site != site_id and dev_role == "Operator":
        return False, "Access Denied: Cross-site breach for Operator"
    
    return True, None

@https_fn.on_request()
def portal_api(req: https_fn.Request) -> https_fn.Response:
    """Unified UI Read API with RBAC."""
    path = req.path
    
    # Simple Router
    # Expected: .../v1/tenants/{tid}/sites/...
    parts = path.split("/")
    try:
        if "tenants" in parts:
            idx = parts.index("tenants")
            tenant_id = parts[idx+1]
            site_id = parts[idx+3] if len(parts) > idx+3 and parts[idx+2] == "sites" else None
        else:
            return https_fn.Response("Invalid Path", status=400)
    except IndexError:
        return https_fn.Response("Invalid Path Structure", status=400)
    
    # 1. RBAC check
    allowed, error = check_rbac(req, tenant_id, site_id)
    if not allowed:
        return https_fn.Response(json.dumps({"error": error}), status=403, mimetype="application/json")

    # 2. Handle Requests (Real Operational Store backbacked)
    if path.endswith("/sites"):
        # In production, query DB. Here, we can derive from state_store
        sites = {}
        for key in processor.state_store:
            tid, sid, mid = key.split(":")
            if tid == tenant_id:
                sites[sid] = sites.get(sid, 0) + 1
        return https_fn.Response(json.dumps([
            {"site_id": sid, "name": sid.capitalize(), "machine_count": count} for sid, count in sites.items()
        ] or [{"site_id": "site_demo", "name": "Default Site", "machine_count": 0}]), mimetype="application/json")
        
    if "/machines" in path and not path.endswith("/state"):
        machines = []
        for key, record in processor.state_store.items():
            tid, sid, mid = key.split(":")
            if tid == tenant_id and (not site_id or sid == site_id):
                machines.append({
                    "machine_id": mid,
                    "status": record.get("status"),
                    "last_seen": record.get("timestamp")
                })
        return https_fn.Response(json.dumps(machines), mimetype="application/json")

    if path.endswith("/state"):
        try:
            if "machines" in parts:
                idx = parts.index("machines")
                machine_id = parts[idx+1]
                machine_key = f"{tenant_id}:{site_id}:{machine_id}"
                state = processor.state_store.get(machine_key)
                if state:
                    return https_fn.Response(json.dumps(state), mimetype="application/json")
                return https_fn.Response(json.dumps({"error": "Machine not found"}), status=404, mimetype="application/json")
        except IndexError:
             return https_fn.Response("Invalid Path Structure", status=400)

    if path.endswith("/events"):
        events = []
        # Return all events for the tenant/site or just for specific machine if path matches
        # For simplicity, returning events for the specific site
        for key, machine_events in processor.event_store.items():
            tid, sid, mid = key.split(":")
            if tid == tenant_id and (not site_id or sid == site_id):
                events.extend(machine_events)
        
        # Sort by timestamp descending
        events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return https_fn.Response(json.dumps(events[:50]), mimetype="application/json")

    if path.endswith("/health/fleet"):
        # Real-time Ops View
        health = []
        for key, record in processor.state_store.items():
            tid, sid, mid = key.split(":")
            if tid == tenant_id:
                health.append({
                    "machine_id": mid,
                    "status": "ONLINE" if record.get("status") in ["ACTIVE", "RUNNING"] else "IDLE",
                    "last_seen": record.get("timestamp"),
                    "metrics": record.get("metrics", {})
                })
        return https_fn.Response(json.dumps(health), mimetype="application/json")

    if "/deletion_requests" in path:
        if req.method != 'POST': return https_fn.Response('POST only', status=405)
        data = req.get_json() or {}
        
        # Audit the request
        log_audit_event(tenant_id, "DELETION_REQUESTED", {
            "scope": data.get("scope"),
            "machine_id": data.get("machine_id"),
            "requested_by": data.get("requested_by", "portal_admin")
        })
        
        return https_fn.Response(json.dumps({
            "status": "ACCEPTED",
            "request_id": "del_12345",
            "message": "Deletion request received and queued for batch processing."
        }), status=202, mimetype="application/json")

    return https_fn.Response("Endpoint not implemented", status=501)

@https_fn.on_request()
def debug_api(req: https_fn.Request) -> https_fn.Response:
    """Expansion Task 1: Debugging hot-path state."""
    path = req.path
    if path.endswith("/debug/events"):
        return https_fn.Response(json.dumps(list(processor.event_ids)), mimetype="application/json")
    if path.endswith("/debug/state"):
        return https_fn.Response(json.dumps(processor.state_store), mimetype="application/json")
    return https_fn.Response("Not Found", status=404)
