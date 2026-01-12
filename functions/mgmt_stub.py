from flask import Flask, request, jsonify
import uuid
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mgmt_stub")

ENROLLED_DEVICES = {}

@app.route('/enroll', methods=['POST'])
def enroll():
    data = request.get_json() or {}
    device_id = str(uuid.uuid4())
    logger.info(f"Enrolling device: {device_id}")
    
    response = {
        "device_id": device_id,
        "tenant_id": "tenant_demo",
        "site_id": "site_demo",
        "channel": "dev",
        "config_version": 1,
        "config": {
            "SCAN_INTERVAL_SECONDS": 30,
            "UPLOAD_INTERVAL_SECONDS": 10,
            "pending_manual_enrollments": []
        }
    }
    ENROLLED_DEVICES[device_id] = response
    return jsonify(response)

@app.route('/get_config', methods=['POST'])
def get_config():
    data = request.get_json() or {}
    device_id = data.get("device_id")
    logger.info(f"Config request from {device_id}")
    
    # Simulate a dynamic update every now and then (optional)
    return jsonify({
        "changed": False,
        "config_version": 1,
        "config": ENROLLED_DEVICES.get(device_id, {}).get("config", {})
    })

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.get_json() or {}
    logger.info(f"Heartbeat from {data.get('device_id')}")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(port=8090)
