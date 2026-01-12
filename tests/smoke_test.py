import requests
import time
import sys

EMULATOR_URL = "http://127.0.0.1:5001/simco-ai-prod/us-central1"
INGEST_URL = "http://127.0.0.1:8080"
CHAT_URL = "http://127.0.0.1:8081"

def run_smoke_tests():
    print("🚀 Starting SIMCO AI Serverless Smoke Tests...")
    
    # Test 1: Cloud Function (Ingestion)
    print("\n[TEST 1] Ingesting Telemetry...")
    payload = {
        "machine_id": "SMOKE-TEST-CNC",
        "telemetry": {"spindle_load": 42, "status": "TESTING"}
    }
    try:
        res = requests.post(INGEST_URL, json=payload, timeout=5)
        if res.status_code == 200:
            print("✅ SUCCESS: Telemetry accepted by Cloud Function.")
        else:
            print(f"❌ FAILED: Status {res.status_code} | {res.text}")
    except Exception as e:
        print(f"❌ FAILED: Connection error. Is Firebase Emulator running? ({e})")

    # Test 2: AI Investigator
    print("\n[TEST 2] Querying AI Investigator...")
    try:
        res = requests.post(CHAT_URL, json={"query": "Any anomalies?"}, timeout=5)
        if res.status_code == 200:
            print(f"✅ SUCCESS: AI responded: {res.json()['response']}")
        else:
            print(f"❌ FAILED: Status {res.status_code}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

    # Test 3: Static Site Availability (Local)
    print("\n[TEST 3] Checking Hosting Assets...")
    import os
    if os.path.exists("web/index.html"):
        print("✅ SUCCESS: index.html exists in web directory.")
    else:
        print("❌ FAILED: web/index.html missing.")

if __name__ == "__main__":
    # If 'run' argument present, just run once. Else maybe wait for emulator.
    run_smoke_tests()
