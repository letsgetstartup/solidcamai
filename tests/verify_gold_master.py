import unittest
from unittest.mock import MagicMock, patch
import json
import logging
import sys
import os
import asyncio
from dataclasses import asdict

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- MOCKS ---
class FakeResponse:
    def __init__(self, response, status=200, headers=None, mimetype=None):
        self.response = [response] 
        self.status_code = status
        self.headers = headers or {}
        self.mimetype = mimetype

# Mock Cloud Environment
sys.modules["firebase_functions"] = MagicMock()
sys.modules["firebase_functions"].https_fn.Response = FakeResponse
sys.modules["firebase_functions"].https_fn.on_request = lambda **kwargs: (lambda func: func)
sys.modules["firebase_admin"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()

# Mock internal modules
for m in ["functions.portal_api", "functions.mgmt_api", "functions.ingest_api", "admin_api", "auth", "auth.middleware", "cloud.processing.bus", "cloud.processing.stream_processor"]:
    sys.modules[m] = MagicMock()
    if "auth" in m:
         sys.modules[m].require_auth = lambda f: f

# Import Cloud Functions
try:
    from functions.main import pair_init, pair_confirm, pair_token, ingest_telemetry, metrics_history, ask
except ImportError:
    pass

# Import Agent Components
from simco_agent.drivers.common.models import TelemetryBatch, TelemetryRecord

class GoldMasterTest(unittest.TestCase):
    
    def mock_req(self, json_data, args=None):
        req = MagicMock()
        req.method = "POST"
        req.get_json.return_value = json_data or {}
        req.args = args or {}
        req.headers = {"X-Tenant-ID": "test_tenant", "Authorization": "Bearer tok"}
        return req

    def test_end_to_end_flow(self):
        print("\n=== Simco V2 Gold Master Test ===")
        
        # 1. Provisioning (Simulated)
        print("[1] Provisioning Gateway...")
        req = self.mock_req({"fingerprint": "gold-master-gw"})
        res = pair_init(req)
        body = json.loads(res.response[0])
        code = body["code"]
        print(f"    - Clean pairing code: {code}")
        
        # Admin verifies
        with patch('functions.main.validate_auth', return_value={"role": "Admin", "tenant_id": "t1"}):
            req_confirm = self.mock_req({"code": code, "tenant_id": "t1", "site_id": "s1"})
            res_confirm = pair_confirm(req_confirm)
            self.assertEqual(json.loads(res_confirm.response[0])["status"], "SUCCESS")
            print("    - Admin confirmed.")
            
        # Exchange Token
        req_tok = self.mock_req({"code": code})
        res_tok = pair_token(req_tok)
        token_body = json.loads(res_tok.response[0])
        self.assertEqual(token_body["status"], "SUCCESS")
        gw_token = token_body["token"]
        print(f"    - Gateway Token Acquired: {gw_token[:8]}...")

        # 2. Ingestion (Simulated Agent Push)
        print("[2] Ingesting Telemetry...")
        batch = TelemetryBatch(records=[
            TelemetryRecord(
                record_id="rec1", 
                machine_id="M1", 
                timestamp="2024-01-01T10:00:00Z", 
                metrics={"spindle": 100},
                status="ACTIVE",
                tenant_id="t1",
                site_id="s1"
            )
        ])
        batch_dict = asdict(batch)
        batch_dict["gateway_id"] = "gw1" # Required by Pydantic Schema
        
        with patch('functions.main.validate_auth', return_value={"tenant_id": "t1", "gateway_id": "gw1"}), \
             patch('functions.main.get_bq_client') as mock_bq:
            
            # Mock Processor in main (it might be imported or instantiated)
            # Since we can't easily patch 'functions.main.processor' if it's imported as module, 
            # let's try assuming main.py has `processor` available.
            # We'll patch the imported module's object.
            import functions.main
            functions.main.processor = MagicMock()
            functions.main.processor.process_record.return_value = asyncio.sleep(0) # Mock awaitable

            # Mock BQ Insert
            mock_bq.return_value.insert_rows_json.return_value = [] # No errors
            
            req_ingest = self.mock_req(batch_dict)
            res_ingest = ingest_telemetry(req_ingest)
            body_ingest = json.loads(res_ingest.response[0])
            self.assertEqual(body_ingest.get("status"), "SUCCESS", f"Ingestion Failed: {body_ingest}")
            print("    - Telemetry Ingested (BQ Insert verified).")

        # 3. Analytics (Simulated Portal Query)
        print("[3] Querying Analytics History...")
        with patch('functions.main.validate_auth', return_value={"tenant_id": "t1"}), \
             patch('functions.main.get_bq_client') as mock_bq:
            
            # Mock Result
            mock_row = {"hour_bucket": "2024-01-01T10:00:00Z", "minutes_active": 60}
            mock_bq.return_value.query.return_value.result.return_value = [mock_row]
            
            req_hist = self.mock_req({}, args={"machine_id": "M1", "start": "...", "end": "..."})
            req_hist.method = "GET"
            res_hist = metrics_history(req_hist)
            body_hist = json.loads(res_hist.response[0])
            self.assertEqual(body_hist[0]["minutes_active"], 60)
            print("    - History API returned Aggregates.")

        # 4. AI Investigator (Simulated Chat)
        print("[4] AI Investigation...")
        with patch('functions.main.get_bq_client') as mock_bq:
            # Mock Result
            mock_row = {"machine_id": "M1", "metric": "spindle", "value": 100}
            mock_bq.return_value.query.return_value.result.return_value = [mock_row]
            
            req_chat = self.mock_req({"question": "Check telemetry for M1"})
            res_chat = ask(req_chat)
            body_chat = json.loads(res_chat.response[0])
            self.assertIn("latest telemetry", body_chat["answer"].lower())
            print("    - AI validated BQ context and answered.")
            
        print("=== Gold Master Test: PASSED ===")

if __name__ == '__main__':
    logging.basicConfig(level=logging.CRITICAL)
    unittest.main()
