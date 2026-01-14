from firebase_functions import https_fn
import json

def dispatch(req: https_fn.Request) -> https_fn.Response:
    """Stub for Portal API."""
    return https_fn.Response(json.dumps({"message": "Portal API Stub"}), status=501, mimetype="application/json")
