import requests
import json
import sys

# Config
API_KEY = "AIzaSyC7fhKNYuSMj2j35KQnC5OFbt_Jb-M9Tzw"
EMAIL = "smoke_test_full_cycle@simco.ai"
PASSWORD = "password123"
API_BASE = "https://portal-api-i6yvrrps6q-uc.a.run.app"

def get_id_token():
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
        "returnSecureToken": True
    }
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        print(f"Auth Failed: {resp.text}")
        sys.exit(1)
    return resp.json()["idToken"]

def debug_whoami(token):
    url = f"{API_BASE}/portal_api/whoami"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Checking {url} ---")
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")

def debug_machines(token):
    # Try the problematic endpoint
    url = f"{API_BASE}/portal_api/v1/tenants/tenant_demo/sites/site_demo/machines"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Checking {url} ---")
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")

if __name__ == "__main__":
    print("Getting Token...")
    token = get_id_token()
    print("Token received.")
    
    debug_whoami(token)
    debug_machines(token)
