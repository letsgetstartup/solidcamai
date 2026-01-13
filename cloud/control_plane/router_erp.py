from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .db import get_db
from .models_erp import ErpConnection, ErpEntityState, ErpMachineMap
from .schemas_erp import ErpConnectionCreate, ErpConnectionOut, ErpSyncRequest, ErpMachineMapUpsert

from cloud.erp.connectors.registry import get_connector_class
from cloud.erp.connectors.sap_b1_service_layer import SapB1ServiceLayerConfig
from cloud.erp.bq_writer import ErpBigQueryWriter
from cloud.erp.ingestion import ErpIngestionOrchestrator, EntitySyncState

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}/erp", tags=["erp"])

# ---- Secret handling (Best practice: Secret Manager) ----
# For this repo-ready implementation, we store secrets in ENV or a placeholder secret store.
# Replace these functions with GCP Secret Manager integration in production.
_SECRET_STORE: Dict[str, Dict[str, str]] = {}

def store_secret(username: str, password: str) -> str:
    ref = f"devsecret://{uuid.uuid4()}"
    _SECRET_STORE[ref] = {"username": username, "password": password}
    return ref

def load_secret(secret_ref: str) -> Dict[str, str]:
    if secret_ref not in _SECRET_STORE:
        raise KeyError("secret_ref not found")
    return _SECRET_STORE[secret_ref]

def get_bq_writer() -> ErpBigQueryWriter:
    # Keep consistent with SIMCO BigQuery usage
    import os
    project_id = os.getenv("SIMCO_GCP_PROJECT_ID", "simco-ai-prod")
    dataset_id = os.getenv("SIMCO_BQ_ANALYTICS_DATASET", "simco_analytics_prod")
    table_id = os.getenv("SIMCO_BQ_ERP_RAW_TABLE", "erp_raw")
    return ErpBigQueryWriter(project_id, dataset_id, table_id)

@router.post("/connections", response_model=ErpConnectionOut)
async def create_connection(tenant_id: str, req: ErpConnectionCreate, db: AsyncSession = Depends(get_db)):
    conn_id = str(uuid.uuid4())
    secret_ref = store_secret(req.username, req.password)

    conn = ErpConnection(
        id=conn_id,
        tenant_id=tenant_id,
        provider=req.provider,
        display_name=req.display_name,
        base_url=req.base_url,
        company_db=req.company_db,
        secret_ref=secret_ref,
        enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(conn)
    await db.commit()

    return ErpConnectionOut(
        id=conn.id,
        tenant_id=conn.tenant_id,
        provider=conn.provider,
        display_name=conn.display_name,
        base_url=conn.base_url,
        company_db=conn.company_db,
        enabled=conn.enabled,
    )

@router.get("/connections", response_model=List[ErpConnectionOut])
async def list_connections(tenant_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ErpConnection).where(ErpConnection.tenant_id == tenant_id))
    items = res.scalars().all()
    return [
        ErpConnectionOut(
            id=c.id, tenant_id=c.tenant_id, provider=c.provider, display_name=c.display_name,
            base_url=c.base_url, company_db=c.company_db, enabled=c.enabled
        ) for c in items
    ]

@router.post("/connections/{connection_id}/test")
async def test_connection(tenant_id: str, connection_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ErpConnection).where(ErpConnection.tenant_id == tenant_id, ErpConnection.id == connection_id)
    )
    conn = res.scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Connection not found")

    secret = load_secret(conn.secret_ref)

    connector_cls = get_connector_class(conn.provider)
    if conn.provider == "sap_b1_service_layer":
        connector = connector_cls(SapB1ServiceLayerConfig(
            base_url=conn.base_url,
            company_db=conn.company_db or "",
            username=secret["username"],
            password=secret["password"],
            verify_tls=True,
        ))
    else:
        raise HTTPException(400, f"Unsupported provider: {conn.provider}")

    status = await connector.healthcheck()
    return status

@router.post("/connections/{connection_id}/sync")
async def sync_connection(tenant_id: str, connection_id: str, req: ErpSyncRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ErpConnection).where(ErpConnection.tenant_id == tenant_id, ErpConnection.id == connection_id)
    )
    conn = res.scalar_one_or_none()
    if not conn:
        raise HTTPException(404, "Connection not found")

    secret = load_secret(conn.secret_ref)
    connector_cls = get_connector_class(conn.provider)

    if conn.provider != "sap_b1_service_layer":
        raise HTTPException(400, f"Unsupported provider: {conn.provider}")

    connector = connector_cls(SapB1ServiceLayerConfig(
        base_url=conn.base_url,
        company_db=conn.company_db or "",
        username=secret["username"],
        password=secret["password"],
        verify_tls=True,
    ))

    writer = get_bq_writer()
    orchestrator = ErpIngestionOrchestrator(writer)

    entities = connector.list_entities()
    if req.entities:
        wanted = set(req.entities)
        entities = [e for e in entities if e.name in wanted]

    results: Dict[str, Any] = {}
    for entity in entities:
        # load entity state
        st_res = await db.execute(
            select(ErpEntityState).where(
                ErpEntityState.connection_id == conn.id,
                ErpEntityState.entity_name == entity.name
            )
        )
        st = st_res.scalar_one_or_none()
        state = EntitySyncState(
            last_successful_sync_ts=st.last_successful_sync_ts if st else None,
            last_source_updated_at_seen=st.last_source_updated_at_seen if st else None,
            last_error=st.last_error if st else None,
        )

        new_state = await orchestrator.sync_entity(
            connector=connector,
            tenant_id=tenant_id,
            connection_id=conn.id,
            source_system="sap_b1",
            entity=entity,
            state=state,
            page_size=req.page_size,
        )

        # upsert entity state
        if not st:
            st = ErpEntityState(connection_id=conn.id, entity_name=entity.name)
            db.add(st)

        st.last_successful_sync_ts = new_state.last_successful_sync_ts
        st.last_source_updated_at_seen = new_state.last_source_updated_at_seen
        st.last_error = new_state.last_error
        st.updated_at = datetime.utcnow()

        results[entity.name] = {
            "last_successful_sync_ts": (new_state.last_successful_sync_ts.isoformat() if new_state.last_successful_sync_ts else None),
            "last_source_updated_at_seen": (new_state.last_source_updated_at_seen.isoformat() if new_state.last_source_updated_at_seen else None),
            "last_error": new_state.last_error,
        }

    await db.commit()
    return {"ok": True, "results": results}

@router.post("/machine-map")
async def upsert_machine_map(tenant_id: str, req: ErpMachineMapUpsert, db: AsyncSession = Depends(get_db)):
    row = ErpMachineMap(
        tenant_id=tenant_id,
        site_id=req.site_id,
        machine_id=req.machine_id,
        erp_system=req.erp_system,
        erp_resource_code=req.erp_resource_code,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    await db.commit()
    return {"ok": True}
