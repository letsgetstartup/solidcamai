import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Mock firebase_functions for import
import sys
from unittest.mock import MagicMock

class MockResponse:
    def __init__(self, data, status=200, mimetype=None):
        self.data = data
        self.status = status
        self.mimetype = mimetype

mock_https = MagicMock()
mock_https.Response = MockResponse
sys.modules['firebase_functions'] = mock_https
sys.modules['firebase_functions.https_fn'] = mock_https
sys.modules['firebase_admin'] = MagicMock()
sys.modules['firebase_admin.auth'] = MagicMock()
sys.modules['simco_agent.observability.metrics'] = MagicMock()

# Import the function to test
# We need to add the functions dir to path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../functions")))

import main
from main import _bigscreen_summary

# Ensure the mock response is used
main.https_fn.Response = MockResponse

@patch("main.processor")
@patch("main.get_bq_client")
@patch("main.check_rbac")
def test_bigscreen_summary_basic(mock_rbac, mock_bq, mock_processor):
    # Setup mocks
    mock_rbac.return_value = (True, None)
    
    mock_processor.state_store = {
        "t1:s1:m1": {
            "tenant_id": "t1",
            "site_id": "s1",
            "machine_id": "m1",
            "status": "RUNNING",
            "timestamp": "2026-01-13T08:00:00Z",
            "metrics": {"spindle_load": 50}
        }
    }
    mock_processor.event_store = {
        "t1:s1:m1": [
            {"severity": "HIGH", "event_type": "ALARM", "message": "Test Alarm", "timestamp": "2026-01-13T08:01:00Z"}
        ]
    }
    
    # Mock request
    mock_req = MagicMock()
    
    # Call function
    response = _bigscreen_summary(mock_req, "t1", "s1")
    
    # Verify response
    assert response.status == 200
    data = json.loads(response.data)
    
    assert data["tenant_id"] == "t1"
    assert data["site_id"] == "s1"
    assert data["fleet"]["total"] == 1
    assert data["fleet"]["running"] == 1
    assert len(data["machines"]) == 1
    assert data["machines"][0]["machine_id"] == "m1"
    assert data["machines"][0]["status"] == "RUNNING"
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["message"] == "Test Alarm"

@patch("main.check_rbac")
def test_bigscreen_summary_unauthorized(mock_rbac):
    mock_rbac.return_value = (False, "Access Denied")
    mock_req = MagicMock()
    
    response = _bigscreen_summary(mock_req, "t1", "s1")
    
    assert response.status == 403
    data = json.loads(response.data)
    assert data["error"] == "Access Denied"
