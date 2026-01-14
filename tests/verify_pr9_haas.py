import unittest
import threading
import asyncio
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.drivers.loader import SecureDriverLoader
from simco_agent.discovery.selection import DriverSelector

class MockHaasHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/current":
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<MTConnectStreams xmlns:m="urn:mtconnect.org:MTConnectStreams:1.3" xmlns="urn:mtconnect.org:MTConnectStreams:1.3">
  <Header creationTime="2023-10-27T10:00:00Z" sender="HAAS-NGC" instanceId="123" version="1.5.0.12" bufferSize="131072" nextSequence="1000" firstSequence="1" lastSequence="2000"/>
  <Streams>
    <DeviceStream name="HaasVF2" uuid="d1">
      <ComponentStream component="Controller" name="path">
        <Events>
           <Execution dataItemId="exec" sequence="10" timestamp="2023-10-27T10:00:00Z">ACTIVE</Execution>
           <ControllerMode dataItemId="mode" sequence="11" timestamp="2023-10-27T10:00:00Z">AUTOMATIC</ControllerMode>
           <Program dataItemId="pgm" sequence="12" timestamp="2023-10-27T10:00:00Z">O12345</Program>
        </Events>
        <Samples>
           <PathFeedrate dataItemId="feed" sequence="13" timestamp="2023-10-27T10:00:00Z">1500.5</PathFeedrate>
        </Samples>
      </ComponentStream>
      <ComponentStream component="Spindle" name="spindle">
        <Samples>
           <SpindleSpeed dataItemId="sspeed" sequence="14" timestamp="2023-10-27T10:00:00Z">5000</SpindleSpeed>
        </Samples>
      </ComponentStream>
    </DeviceStream>
  </Streams>
</MTConnectStreams>"""
            self.wfile.write(xml.encode("utf-8"))
        elif self.path == "/probe":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)

def run_server(port):
    server = HTTPServer(("127.0.0.1", port), MockHaasHandler)
    server.serve_forever()

class TestHaasDriver(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.port = 7899
        t = threading.Thread(target=run_server, args=(cls.port,), daemon=True)
        t.start()
        time.sleep(1)

    def test_haas_driver_full_lifecycle(self):
        # 1. Use Selector to find manifest (and verify one exists for Haas)
        selector = DriverSelector()
        # Find the haas_mtconnect manifest
        manifest = next((m for m in selector.manifests if m.name == "haas_mtconnect"), None)
        self.assertIsNotNone(manifest)
        print(f"Found Manifest: {manifest.name} Checksum: {manifest.checksum}")
        
        # 2. Secure Load
        loader = SecureDriverLoader()
        # Need to point loader to project root where simco_agent is if strict
        # But our loader logic defaults to simco_agent/drivers/impl relative to itself.
        # This calls for verification.
        
        module = loader.load_driver(manifest)
        self.assertIsNotNone(module)
        print("Secure Load: SUCCESS")
        
        # 3. Instantiate Driver
        driver_class = getattr(module, "HaasMTConnectDriver")
        driver = driver_class(config={"ip": "127.0.0.1", "port": self.port})
        
        # 4. Connect
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        connected = loop.run_until_complete(driver.connect())
        self.assertTrue(connected)
        print("Connect: SUCCESS")
        
        # 5. Collect Metrics
        points = loop.run_until_complete(driver.collect_metrics())
        self.assertTrue(len(points) > 0)
        
        # Verify specific values
        kv = {p.name: p.value for p in points}
        print(f"Metrics: {kv}")
        
        self.assertEqual(kv["execution_state"], "ACTIVE")
        self.assertEqual(kv["controller_mode"], "AUTOMATIC")
        self.assertEqual(kv["spindle_speed"], 5000.0)
        self.assertEqual(kv["path_feedrate"], 1500.5)
        self.assertEqual(kv["program_name"], "O12345")
        
        print("Data Verification: SUCCESS")

if __name__ == '__main__':
    unittest.main()
