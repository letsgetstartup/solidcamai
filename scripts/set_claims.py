import firebase_admin
from firebase_admin import auth, credentials
import sys

# Initialize using default creds (Google Cloud) or rely on existing init if embedded
# For local script, we might need 'GOOGLE_APPLICATION_CREDENTIALS' pointed to a key, 
# OR we can assume `firebase-admin` works if logged in via `gcloud auth application-default login`.
# Let's try default.

if not firebase_admin._apps:
    firebase_admin.initialize_app()

EMAIL = "smoke_test_full_cycle@simco.ai"
CLAIMS = {
    "tenant_id": "tenant_demo",
    "site_id": "site_demo",
    "role": "Manager"
}

def set_claims():
    try:
        user = auth.get_user_by_email(EMAIL)
        print(f"Found user: {user.uid}")
        
        auth.set_custom_user_claims(user.uid, CLAIMS)
        print(f"Successfully set claims for {EMAIL}: {CLAIMS}")
        
        # Verify
        user = auth.get_user(user.uid)
        print(f"Verified Claims: {user.custom_claims}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    set_claims()
