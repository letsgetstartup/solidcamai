import requests
import json
import sys

# Constants
GENERATE_QR_URL = "https://generate-qr-i6yvrrps6q-uc.a.run.app"
GET_CONTEXT_URL = "https://get-mobile-context-i6yvrrps6q-uc.a.run.app"
MACHINE_ID = "siemens_840d_03" # Known active machine from previous test

def verify_mobile_flow():
    print(f"--- 1. Generating QR for {MACHINE_ID} ---")
    qr_url = f"{GENERATE_QR_URL}/mgmt/v1/sites/site_demo/machines/{MACHINE_ID}/qr"
    try:
        resp = requests.post(qr_url)
        if resp.status_code != 200:
            print(f"FAILED: Generate QR returned {resp.status_code}: {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        token = data.get("public_code")
        print(f"SUCCESS: Got Token: {token}")
        
    except Exception as e:
        print(f"FAILED: Exception generating QR: {e}")
        sys.exit(1)

    print(f"\n--- 2. Scanning QR (Getting Context) ---")
    # Path: /mobile/v1/machines/by-token/{token}/context
    ctx_url = f"{GET_CONTEXT_URL}/mobile/v1/machines/by-token/{token}/context"
    try:
        resp = requests.get(ctx_url)
        if resp.status_code != 200:
            print(f"FAILED: Get Context returned {resp.status_code}: {resp.text}")
            sys.exit(1)
            
        ctx = resp.json()
        print("SUCCESS: Received Context Payload")
        print(json.dumps(ctx, indent=2))
        
        # Validation
        if ctx.get("machine", {}).get("id") != MACHINE_ID:
            print(f"ERROR: Machine ID mismatch. Expected {MACHINE_ID}, got {ctx.get('machine', {}).get('id')}")
            sys.exit(1)
            
        if not ctx.get("live_status"):
             print("WARNING: 'live_status' is empty. Did BigQuery ingestion work?")
        else:
             print("VERIFIED: Telemetry Data Present")
             
        if not ctx.get("erp_orders"):
             print("WARNING: 'erp_orders' is empty.")
        else:
             print(f"VERIFIED: {len(ctx['erp_orders'])} ERP Orders Present")
             
    except Exception as e:
        print(f"FAILED: Exception getting context: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_mobile_flow()
