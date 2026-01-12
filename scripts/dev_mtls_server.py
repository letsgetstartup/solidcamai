import argparse
import http.server
import ssl
import json

class MTLSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ping":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"pong")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/heartbeat":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())
        else:
            self.send_error(404)

def run_server(host, port, ca, cert, key, require_client_cert):
    server_address = (host, port)
    httpd = http.server.HTTPServer(server_address, MTLSHandler)
    
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=cert, keyfile=key)
    context.load_verify_locations(cafile=ca)
    
    if require_client_cert:
        context.verify_mode = ssl.CERT_REQUIRED
    
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print(f"mTLS Server running on https://{host}:{port} (require_client_cert={require_client_cert})")
    httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9443)
    parser.add_argument("--ca", required=True)
    parser.add_argument("--server-cert", required=True)
    parser.add_argument("--server-key", required=True)
    parser.add_argument("--require-client-cert", type=str, default="true")
    
    args = parser.parse_args()
    run_server(args.host, args.port, args.ca, args.server_cert, args.server_key, args.require_client_cert.lower() == "true")
