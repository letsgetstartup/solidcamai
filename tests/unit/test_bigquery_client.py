import pytest
from unittest.mock import MagicMock, patch
from simco_agent.cloud.bigquery import BigQueryClient

@pytest.fixture
def mock_bq_client():
    with patch("simco_agent.cloud.bigquery.bigquery.Client") as MockClient:
        client_instance = MockClient.return_value
        
        # Mock dataset().table()
        mock_dataset = MagicMock()
        mock_table = MagicMock()
        client_instance.dataset.return_value = mock_dataset
        mock_dataset.table.return_value = mock_table
        
        # Mock insert_rows_json
        # Returns list of errors (empty list = success)
        client_instance.insert_rows_json.return_value = []
        
        yield client_instance

def test_stream_rows(mock_bq_client):
    bq = BigQueryClient("my-project", "my_dataset", "my_table")
    
    # Verify init called client
    # Note: BQ client init happens in __init__, so mock must be active during init
    # But fixture activates patch before test function starts? Yes.
    
    rows = [{"id": 1, "val": "test"}]
    success = bq.stream_rows(rows)
    
    assert success is True
    mock_bq_client.insert_rows_json.assert_called_once()
    
    args, kwargs = mock_bq_client.insert_rows_json.call_args
    # args[0] is table ref, args[1] is rows
    assert args[1] == rows
