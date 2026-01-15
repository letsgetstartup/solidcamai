import logging
import json
import os
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from simco_agent.db import AsyncSessionLocal, Machine, MachineStatus
from simco_agent.schemas import MachineInfo

logger = logging.getLogger(__name__)

class RegistryService:
    def __init__(self):
        pass

    async def get_enrolled_machines(self) -> list[MachineInfo]:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Machine).where(Machine.status == MachineStatus.ENROLLED)
            )
            rows = result.scalars().all()
            return [
                MachineInfo(
                    mac=r.mac, 
                    ip=r.ip, 
                    vendor=r.vendor, 
                    status="active", # Mapping to Pydantic schema
                    driver_id=r.driver_id
                ) for r in rows
            ]

    async def register_discovered_machine(self, info: MachineInfo):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Machine).where(Machine.mac == info.mac))
            existing = result.scalars().first()
            
            if not existing:
                machine = Machine(
                    mac=info.mac,
                    ip=info.ip,
                    vendor=info.vendor,
                    name=f"Machine-{info.mac[-4:]}",
                    status=MachineStatus.DISCOVERED
                )
                db.add(machine)
                logger.info(f"Discovered new machine: {info.ip}")
            else:
                # Update IP if changed
                if existing.ip != info.ip:
                    existing.ip = info.ip
            await db.commit()

    async def enroll_machine(self, mac: str, name: str, driver_id: str):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Machine).where(Machine.mac == mac))
            machine = result.scalars().first()
            if machine:
                machine.status = MachineStatus.ENROLLED
                machine.name = name
                machine.driver_id = driver_id
                await db.commit()
                logger.info(f"Enrolled machine: {mac} as {name}")

    async def migrate_legacy_registry(self, json_path="machine_registry.json"):
        if not os.path.exists(json_path):
            return
            
        logger.info(f"Migrating legacy registry from {json_path}")
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            
            for m in data:
                # Naively assume legacy entries were 'enrolled' or we enroll them now
                info = MachineInfo(
                    mac=m.get("mac", "unknown"), # Legacy might miss MAC, need robust handling
                    ip=m.get("ip"),
                    vendor=m.get("protocol", "unknown").upper(), # Mapping protocol to vendor loose
                )
                # First ensuring record exists
                await self.register_discovered_machine(info)
                # Then enrolling
                await self.enroll_machine(info.mac, m.get("name", "Legacy Machine"), "generic")
                
            os.rename(json_path, f"{json_path}.bak")
            logger.info("Migration complete.")
        except Exception as e:
            logger.error(f"Migration failed: {e}")


registry = RegistryService()

# --- Legacy JSON Support for Orchestrator ---
def load_registry(path: str = "machine_registry.json") -> list[dict]:
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load registry from {path}: {e}")
        return []

def save_registry(data: list[dict], path: str = "machine_registry.json"):
    if not path:
        return
    try:
        # Atomic write
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.rename(tmp_path, path)
    except Exception as e:
        logger.error(f"Failed to save registry to {path}: {e}")
