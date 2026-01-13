import pytest
import os
import tempfile
from simco_agent.telemetry.buffer import TelemetryBuffer
from simco_agent.drivers.common.models import TelemetryPoint

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_buffer_ops(temp_db):
    buf = TelemetryBuffer(db_path=temp_db)
    
    # 1. Push
    points = [
        TelemetryPoint(name="p1", value=1, timestamp="t1"),
        TelemetryPoint(name="p2", value=2, timestamp="t2"),
        TelemetryPoint(name="p3", value=3, timestamp="t3")
    ]
    buf.push(points)
    
    assert buf.count() == 3
    
    # 2. Pop partial
    ids, payloads = buf.pop_chunk(limit=2)
    assert len(ids) == 2
    assert len(payloads) == 2
    assert payloads[0]["name"] == "p1"
    assert payloads[1]["name"] == "p2"
    
    # 3. Commit
    buf.commit_chunk(ids)
    assert buf.count() == 1
    
    # 4. Pop remaining
    ids2, payloads2 = buf.pop_chunk(limit=10)
    assert len(ids2) == 1
    assert payloads2[0]["name"] == "p3"
    
    # 5. Persistence Check (reopen DB)
    buf2 = TelemetryBuffer(db_path=temp_db)
    # We didn't commit ids2 yet, so it should still be there
    assert buf2.count() == 1
    
    buf2.commit_chunk(ids2)
    assert buf2.count() == 0
