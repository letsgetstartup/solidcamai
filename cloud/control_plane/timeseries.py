from sqlalchemy import Column, String, Float, DateTime, Integer, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import datetime

# Independent Base or shared? Let's use shared Base if possible to keep in same DB for MVP.
# But usually TSDB is separate. For this MVP, we collocate.
from .db import Base

class TelemetryHypertable(Base):
    """
    Represents a high-frequency metric point.
    In a real PG setup, we would convert this to a TimescaleDB hypertable:
    SELECT create_hypertable('telemetry_hypertable', 'time');
    """
    __tablename__ = "telemetry_hypertable"
    
    # Composite PK for partitioning
    # Note: SQLAlchemy might complain about no single PK if we don't handle it right.
    # We use a surrogate ID for simple SQLite compat, but in prod 'time' + 'machine_id' + 'metric' is key.
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    machine_id = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    metric_name = Column(String, nullable=False) # e.g. "spindle_load"
    metric_value = Column(Float, nullable=False)

class TimeseriesService:
    async def write_batch(self, db: AsyncSession, records: List[Dict[str, Any]]):
        """
        Ingests raw telemetry records (JSON) into normalized metric rows.
        """
        ts_rows = []
        for rec in records:
            # rec = {machine_id, timestamp, metrics: {k:v}}
            mid = rec.get("machine_id")
            ts = rec.get("timestamp")
            # Parse TS if string
            if isinstance(ts, str):
                try:
                    ts = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except:
                    ts = datetime.datetime.utcnow()
            
            metrics = rec.get("metrics", {})
            for k, v in metrics.items():
                if isinstance(v, (int, float)):
                    ts_rows.append(TelemetryHypertable(
                        machine_id=mid,
                        timestamp=ts,
                        metric_name=k,
                        metric_value=float(v)
                    ))
        
        if ts_rows:
            db.add_all(ts_rows)
            await db.commit()
            
    async def query_metrics(self, db: AsyncSession, machine_id: str, metric: str, limit: int = 100):
        result = await db.execute(
            select(TelemetryHypertable)
            .where(TelemetryHypertable.machine_id == machine_id)
            .where(TelemetryHypertable.metric_name == metric)
            .order_by(TelemetryHypertable.timestamp.desc())
            .limit(limit)
        )
        return result.scalars().all()

ts_service = TimeseriesService()
