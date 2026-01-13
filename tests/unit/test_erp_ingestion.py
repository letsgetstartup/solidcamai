import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from cloud.erp.ingestion import ErpIngestionOrchestrator, EntitySyncState
from cloud.erp.bq_writer import ErpBigQueryWriter
from cloud.erp.connectors.base import ErpConnector, ErpEntitySpec

# Mock Connector
class MockConnector(ErpConnector):
    async def healthcheck(self):
        return {"ok": True}
    
    def list_entities(self):
        return []

    async def fetch(self, entity, since, page_size=200):
        # Yield 2 items
        yield {"id": "1", "val": "A", "updated_at": "2024-01-01T10:00:00Z"}
        yield {"id": "2", "val": "B", "updated_at": "2024-01-01T10:05:00Z"}

@pytest.mark.asyncio
async def test_orchestrator_sync_flow():
    # Mock Writer
    mock_writer = MagicMock(spec=ErpBigQueryWriter)
    mock_writer.stream_envelopes = MagicMock()
    
    orchestrator = ErpIngestionOrchestrator(mock_writer)
    connector = MockConnector()
    
    entity = ErpEntitySpec("test", "Test", "id", "updated_at")
    state = EntitySyncState()
    
    new_state = await orchestrator.sync_entity(
        connector=connector,
        tenant_id="t1",
        connection_id="c1",
        source_system="mock",
        entity=entity,
        state=state
    )
    
    # Verify records written
    assert mock_writer.stream_envelopes.called
    call_args = mock_writer.stream_envelopes.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0]["entity"] == "test"
    assert call_args[0]["source_pk"] == "1"
    
    # Verify state updated
    assert new_state.last_source_updated_at_seen is not None
    # ISO strings might differ minutely, just check year
    assert "2024-01-01" in new_state.last_source_updated_at_seen.isoformat()
