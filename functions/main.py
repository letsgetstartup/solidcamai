from firebase_functions import https_fn
from firebase_admin import initialize_app
from google.cloud import bigquery
import json
import logging
from datetime import datetime

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
    import sys
    import os
    # Add root to sys.path to find simco_common
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
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
            if loop.is_running():
                loop.create_task(bus.publish([record_data]))
            else:
                loop.run_until_complete(bus.publish([record_data]))
            
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
def enroll_device(req: https_fn.Request) -> https_fn.Response:
    # ... existing code ...
    return https_fn.Response(json.dumps(response), mimetype="application/json")

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
    if "/v1/tenants/" not in path:
        return https_fn.Response("Bad Route", status=404)
        
    parts = path.split("/")
    # Expected: /v1/tenants/{tid}/sites/...
    tenant_id = parts[3]
    
    # 1. RBAC check
    site_id = parts[5] if len(parts) > 5 else None
    allowed, error = check_rbac(req, tenant_id, site_id)
    if not allowed:
        return https_fn.Response(json.dumps({"error": error}), status=403, mimetype="application/json")

    # 2. Handle Requests (Mocked Operational Store)
    if path.endswith("/sites"):
        return https_fn.Response(json.dumps([
            {"site_id": "site_01", "name": "Main Factory", "machine_count": 5},
            {"site_id": "site_dev", "name": "R&D Lab", "machine_count": 2}
        ]), mimetype="application/json")
        
    if "/machines" in path and not path.endswith("/state"):
        return https_fn.Response(json.dumps([
            {"machine_id": "fanuc_01", "status": "ONLINE", "last_seen": datetime.utcnow().isoformat()},
            {"machine_id": "haas_02", "status": "IDLE", "last_seen": datetime.utcnow().isoformat()}
        ]), mimetype="application/json")

    if path.endswith("/state"):
        machine_id = parts[7]
        return https_fn.Response(json.dumps({
            "machine_id": machine_id,
            "status": "ACTIVE",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {"spindle_load": 42.5, "feed_rate": 1200}
        }), mimetype="application/json")

    if path.endswith("/events"):
        return https_fn.Response(json.dumps([
            {"event_id": "ev_001", "type": "ANOMALY_DETECTED", "severity": "HIGH", "timestamp": datetime.utcnow().isoformat()},
            {"event_id": "ev_002", "type": "CONFIG_CHANGED", "severity": "INFO", "timestamp": datetime.utcnow().isoformat()}
        ]), mimetype="application/json")

    if path.endswith("/health/fleet"):
        # Real-time Ops View (Gathered from Heatbeat/Stats store)
        return https_fn.Response(json.dumps([
            {
                "machine_id": "fanuc_01",
                "status": "ONLINE",
                "last_seen": datetime.utcnow().isoformat(),
                "buffer_depth": 12,
                "sync_latency_sec": 45,
                "version": "v3.1.2-GA"
            },
            {
                "machine_id": "haas_02",
                "status": "UNHEALTHY",
                "last_seen": (datetime.utcnow().isoformat()),
                "buffer_depth": 4500,
                "sync_latency_sec": 3600,
                "version": "v3.1.1-GA"
            }
        ]), mimetype="application/json")

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
