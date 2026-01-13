from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .db import Tenant, Site, Gateway

async def create_tenant(db: AsyncSession, tenant_id: str, name: str):
    db_tenant = Tenant(tenant_id=tenant_id, name=name)
    db.add(db_tenant)
    await db.commit()
    await db.refresh(db_tenant)
    return db_tenant

async def get_tenant(db: AsyncSession, tenant_id: str):
    result = await db.execute(select(Tenant).where(Tenant.tenant_id == tenant_id))
    return result.scalars().first()

async def create_site(db: AsyncSession, site_id: str, tenant_id: str, name: str):
    db_site = Site(site_id=site_id, tenant_id=tenant_id, name=name)
    db.add(db_site)
    await db.commit()
    await db.refresh(db_site)
    return db_site

async def get_site(db: AsyncSession, site_id: str):
    result = await db.execute(select(Site).where(Site.site_id == site_id))
    return result.scalars().first()

async def create_gateway(db: AsyncSession, gateway_id: str, tenant_id: str, site_id: str, display_name: str):
    db_gateway = Gateway(gateway_id=gateway_id, tenant_id=tenant_id, site_id=site_id, display_name=display_name)
    db.add(db_gateway)
    await db.commit()
    await db.refresh(db_gateway)
    return db_gateway

async def get_gateway(db: AsyncSession, gateway_id: str):
    result = await db.execute(select(Gateway).where(Gateway.gateway_id == gateway_id))
    return result.scalars().first()
