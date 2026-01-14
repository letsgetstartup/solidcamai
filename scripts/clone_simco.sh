#!/usr/bin/env bash
set -euo pipefail

# Configuration
SIMCO_REPO="https://github.com/letsgetstartup/simco-cloud-ai.git"
WORK_DIR=$(pwd)
SIMCO_DIR="$WORK_DIR/../simco-cloud-ai" # Clone sibling to avoid nesting

echo "==> 1) Clone/Update Simco Repo"
if [ -d "$SIMCO_DIR/.git" ]; then
    echo "Updating existing repo at $SIMCO_DIR..."
    (cd "$SIMCO_DIR" && git pull)
else
    echo "Cloning Simco repo to $SIMCO_DIR..."
    git clone "$SIMCO_REPO" "$SIMCO_DIR"
fi

echo "==> 2) Copy Simco frontend 1:1"
rm -rf web_simco_public
mkdir -p web_simco_public
echo "Copying assets..."
cp -R "$SIMCO_DIR/public/"* web_simco_public/

echo "==> Preflight: Verifying script.js calls /ask"
if grep -q "fetch('/ask'" web_simco_public/script.js; then
    echo "Confirmed: script.js calls /ask"
else
    echo "WARNING: Could not find fetch('/ask') in script.js. Proceeding, but verification needed."
fi

echo "==> 3) Patch firebase.json for Multi-Site Hosting"
python3 - <<'PY'
import json
from pathlib import Path

p = Path("firebase.json")
try:
    cfg = json.loads(p.read_text())
except FileNotFoundError:
    print("Error: firebase.json not found")
    exit(1)

functions = cfg.get("functions")
hosting = cfg.get("hosting")

# Ensure hosting is a list or convert if single object
if isinstance(hosting, dict):
    # This identifies the CURRENT/OLD single site config
    prod_hosting = dict(hosting)
    prod_hosting["target"] = "prod"
    existing_hosting_list = [prod_hosting]
elif isinstance(hosting, list):
    # Already multi-site? We will append or update
    existing_hosting_list = hosting
else:
    print("Error: hosting config is invalid type")
    exit(1)

# Check if 'prod' exists, if not assume the first one is meant to be prod or create it
# For simplicity, if we converted from dict, we have 'prod'.
# If it was already a list, we leave it alone unless it's missing target 'simco'

simco_hosting = {
    "target": "simco",
    "public": "web_simco_public",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
        {"source": "/ask", "function": "ask"},
        {"source": "**", "destination": "/index.html"}
    ]
}

# Remove existing 'simco' target if present to overwrite
final_hosting = [h for h in existing_hosting_list if h.get("target") != "simco"]
final_hosting.append(simco_hosting)

out = {}
if functions:
    out["functions"] = functions
out["hosting"] = final_hosting

p.write_text(json.dumps(out, indent=4) + "\n")
print(f"firebase.json patched. Hosting targets: {[h.get('target') for h in final_hosting]}")
PY

echo "==> 4) Inject 'ask' function into functions/main.py"
python3 - <<'PY'
from pathlib import Path

p = Path("functions/main.py")
s = p.read_text()

if "def ask(" in s:
    print("ask() already exists - skipping insert.")
else:
    insert = r'''

# === Simco Chat Compatibility: /ask ===
# Simco frontend POSTs to /ask and expects JSON: {"answer": str, "follow_up": [...], "visualization": {...}}
# The UI sends header X-Tenant-ID (hardcoded as 'test_tenant' in simco public/script.js).
# We keep the UI untouched and adapt here.
@https_fn.on_request()
def ask(req: https_fn.Request) -> https_fn.Response:
    if req.method == "OPTIONS":
        return https_fn.Response(
            "",
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Tenant-ID",
            },
        )

    if req.method != "POST":
        return https_fn.Response(
            json.dumps({"error": "POST only"}),
            status=405,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    data = req.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    site_id = (data.get("site_id") or "test_site").strip()

    tenant_id = (req.headers.get("X-Tenant-ID") or "").strip()
    if not tenant_id:
        return https_fn.Response(
            json.dumps({"error": "UNAUTHORIZED", "details": "Missing X-Tenant-ID"}),
            status=401,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    # Best-practice: alias Simco demo tenant -> SolidCamAI demo tenant
    if tenant_id == "test_tenant":
        tenant_id = "tenant_demo"

    if not question:
        return https_fn.Response(
            json.dumps({"error": "MISSING_QUESTION"}),
            status=400,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    # Use SolidCamAI's existing BigQuery config pattern
    dataset = os.environ.get("BQ_DATASET", "simco_telemetry")
    bq = get_bq_client()

    # Use parameterized query (no string interpolation of tenant/site)
    sql = f"""
    SELECT machine_id, COUNT(1) AS event_count
    FROM `{dataset}.raw_events`
    WHERE tenant_id = @tenant_id
      AND site_id = @site_id
      AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    GROUP BY machine_id
    ORDER BY event_count DESC
    LIMIT 10
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("tenant_id", "STRING", tenant_id),
            bigquery.ScalarQueryParameter("site_id", "STRING", site_id),
        ]
    )

    try:
        rows = [dict(r) for r in bq.query(sql, job_config=job_config).result()]
    except Exception as e:
        logger.error(f"/ask BigQuery error: {e}")
        return https_fn.Response(
            json.dumps({"error": "BQ_ERROR", "details": str(e)}),
            status=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    if not rows:
        resp = {
            "answer": f"No events found in the last 24h for tenant={tenant_id}, site={site_id}.\n\nQuestion: {question}",
            "follow_up": [],
            "visualization": {}
        }
    else:
        viz = {
            "type": "bar",
            "title": "Event count by machine (last 24h)",
            "labels": [r.get("machine_id") for r in rows],
            "datasets": [{"label": "events", "data": [r.get("event_count") for r in rows]}],
        }
        resp = {
            "answer": f"Top machines by event count (last 24h). Highest: {rows[0].get('machine_id')} = {rows[0].get('event_count')}.\n\nQuestion: {question}",
            "follow_up": [
                "Which machines had the most ALARM events in the last 7 days?",
                "Show daily trend of events for the last week.",
                "Which machine had the most downtime seconds yesterday?"
            ],
            "visualization": viz
        }

    return https_fn.Response(
        json.dumps(resp),
        status=200,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )

# === End /ask ===
'''
    p.write_text(s + "\n" + insert)
    print("Inserted ask() into functions/main.py")
PY

echo "==> Done. Ready for deployment."
