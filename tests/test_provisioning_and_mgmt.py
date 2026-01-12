import unittest
import os
import json
import shutil
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import uuid
from simco_agent.core.device_state import DeviceState
from simco_agent.core.provisioning import ensure_enrolled
from simco_agent.config import settings

class ManagementStubHandler(BaseHTTPRequestHandler):
    STATE = {"devices": {}, "config_version": 1, "config": {"scan_interval_seconds": 60}}

    def _json(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode() or "{}")
        
        if self.path == "/enroll":
            if data.get("bootstrap_token") != "devtoken":
                return self._json(403, {"error": "bad token"})
            device_id = str(uuid.uuid4())
            self.STATE["devices"][device_id] = {"tenant_id": "tenant_demo", "site_id": "site_demo", "config_version": self.STATE["config_version"]}
            return self._json(200, {
                "device_id": device_id,
                "tenant_id": "tenant_demo",
                "site_id": "site_demo",
                "channel": "dev",
                "config_version": self.STATE["config_version"],
                "config": self.STATE["config"]
            })
        
        if self.path == "/heartbeat":
            return self._json(200, {"status": "ok"})
        
        return self._json(404, {"error": "not found"})

    def log_message(self, *args): return

class TestProvisioningAndMgmt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 8090), ManagementStubHandler)
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self.test_state_file = ".tmp_test_device_state.json"
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)
        settings.DEVICE_STATE_FILE = self.test_state_file
        settings.MGMT_BASE_URL = "http://127.0.0.1:8090"
        settings.BOOTSTRAP_TOKEN = "devtoken"

    def tearDown(self):
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)

    def test_enrollment_lifecycle(self):
        state = DeviceState(self.test_state_file)
        self.assertFalse(state.is_enrolled)
        
        # 1. First Enrollment
        ensure_enrolled(state)
        self.assertTrue(state.is_enrolled)
        device_id_1 = state.device_id
        self.assertEqual(state.data["tenant_id"], "tenant_demo")
        
        # 2. Idempotent Second Run (should not re-enroll)
        ensure_enrolled(state)
        self.assertEqual(state.device_id, device_id_1)
        print(f"✅ Enrollment Verified: {device_id_1}")

    def test_persistence(self):
        state = DeviceState(self.test_state_file)
        state.update(device_id="TEST_ID", tenant_id="T1")
        
        # Load in new instance
        state2 = DeviceState(self.test_state_file)
        self.assertEqual(state2.device_id, "TEST_ID")
        print("✅ Persistence Verified.")

if __name__ == "__main__":
    unittest.main()
