from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .db import DriverMetadata
import logging

logger = logging.getLogger(__name__)

class DriverHubService:
    async def get_drivers(self, db: AsyncSession):
        result = await db.execute(select(DriverMetadata))
        return result.scalars().all()

    async def get_driver_version(self, db: AsyncSession, driver_id: str, version: str):
        result = await db.execute(
            select(DriverMetadata)
            .where(DriverMetadata.driver_id == driver_id)
            .where(DriverMetadata.version == version)
        )
        return result.scalars().first()

    async def seed_defaults(self, db: AsyncSession):
        """
        Seeds standard drivers if they don't exist.
        """
        defaults = [
            {
                "driver_id": "mtconnect", 
                "version": "1.0.0", 
                "download_url": "https://storage.googleapis.com/simco-drivers/mtconnect-1.0.0.py",
                "shasum": "sha256:fake-hash-123"
            },
            {
                "driver_id": "opcua", 
                "version": "1.0.0", 
                "download_url": "https://storage.googleapis.com/simco-drivers/opcua-1.0.0.py",
                "shasum": "sha256:fake-hash-456"
            },
            {
                "driver_id": "modbus", 
                "version": "1.0.0", 
                "download_url": "https://storage.googleapis.com/simco-drivers/modbus-1.0.0.py",
                "shasum": "sha256:fake-hash-789"
            },
        ]
        
        for d in defaults:
            existing = await self.get_driver_version(db, d["driver_id"], d["version"])
            if not existing:
                logger.info(f"Seeding driver {d['driver_id']} v{d['version']}")
                db.add(DriverMetadata(**d))
        
        await db.commit()

driver_hub = DriverHubService()
