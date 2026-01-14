import unittest
import logging
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import sys
import os
import time

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from simco_agent.discovery.probes.mtconnect import MTConnectProbe
from simco_agent.discovery.probes.opcua import OPCUAProbe

# --- Mock MTConnect Server ---
class MockMTConnectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/current":
            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            # Minimal XML with Namespace and Header
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<MTConnectStreams xmlns:m="urn:mtconnect.org:MTConnectStreams:1.3" xmlns="urn:mtconnect.org:MTConnectStreams:1.3">
  <Header creationTime="2023-10-27T10:00:00Z" sender="MAZAK-SMARTBOX" instanceId="123" version="1.5.0.12" bufferSize="131072" nextSequence="1000" firstSequence="1" lastSequence="2000"/>
  <Streams>
  </Streams>
</MTConnectStreams>"""
            self.wfile.write(xml.encode("utf-8"))
        else:
            self.send_response(404)

def run_http_server(port):
    server = HTTPServer(("127.0.0.1", port), MockMTConnectHandler)
    server.serve_forever()

# --- Mock TCP Server (OPC UA Stakeholder) ---
def run_tcp_server(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", port))
    s.listen(1)
    try:
        conn, addr = s.accept()
        conn.close()
    except:
        pass
    s.close()
    
class TestHandshake(unittest.TestCase):
    
    def test_mtconnect_probe(self):
        # Configure logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Start Server
        port = 8899
        t = threading.Thread(target=run_http_server, args=(port,), daemon=True)
        t.start()
        time.sleep(1) # Wait for startup
        
        # Run Probe
        probe = MTConnectProbe()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        fp = loop.run_until_complete(probe.run("127.0.0.1", port))
        
        self.assertIsNotNone(fp)
        print(f"MTConnect FP: {fp}")
        self.assertEqual(fp.vendor, "MAZAK-SMARTBOX")
        self.assertEqual(fp.controller_version, "1.5.0.12")
        self.assertEqual(fp.protocol, "mtconnect")

    def test_opcua_probe(self):
        # Start Dummy TCP
        port = 4842
        t = threading.Thread(target=run_tcp_server, args=(port,), daemon=True)
        t.start()
        time.sleep(0.5)

        probe = OPCUAProbe()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        fp = loop.run_until_complete(probe.run("127.0.0.1", port))
        
        self.assertIsNotNone(fp)
        print(f"OPC UA FP: {fp}")
        self.assertEqual(fp.protocol, "opc_ua")
        self.assertEqual(fp.evidence["port_open"], port)

if __name__ == '__main__':
    unittest.main()
