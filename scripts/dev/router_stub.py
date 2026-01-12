import sys
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure we can import from project root
sys.path.append(os.getcwd())

from functions.main import ingest_telemetry, portal_api
from cloud.processing.stream_processor import processor

app = Flask(__name__)
# Enable CORS for UI
CORS(app) 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dev_router")

# Wrapper to adapt Flask request to functions-framework signature (which often mimics flask anyway)
# functions-framework passes a flask.Request object.

@app.route("/", methods=["POST"])
def handle_ingest():
    # Ingest is at root / for port 8081 usually, but here we might map it to /ingest
    # or just route based on request structure (bad idea).
    # Let's mirror the specific paths.
    return ingest_telemetry(request)

@app.route("/ingest", methods=["POST"])
def handle_ingest_explicit():
    return ingest_telemetry(request)

@app.route("/portal_api/<path:subpath>", methods=["GET", "POST"])
def handle_portal(subpath):
    # Portal API expects /v1/...
    # But functions framework target usually handles the root.
    # We need to ensure req.path matches what portal_api expects.
    # portal_api logic: path = req.path
    # if I request /portal_api/v1/..., req.path might be /portal_api/v1/...
    # portal_api checks `if "/v1/tenants/" not in path`.
    logger.info(f"Portal Request: {request.path}")
    logger.info(f"Portal Headers: {dict(request.headers)}")
    return portal_api(request)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8081))
    logger.info(f"Starting Unified Dev Router on port {port}")
    # Run with threading to allow concurrent requests (though standard flask dev server is blocking-ish)
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
