#!/usr/bin/env bash
set -euo pipefail

# Smoke test for Big Screen Wallboard API
# Usage: ./smoke_bigscreen.sh [TENANT_ID] [SITE_ID]

TENANT="${1:-tenant_demo}"
SITE="${2:-site_demo}"
PORT="${3:-8081}"

echo "Testing Big Screen Summary for ${TENANT}/${SITE} on port ${PORT}..."

curl -s \
  -H "X-Dev-Role: admin" \
  -H "X-Dev-Tenant: ${TENANT}" \
  -H "X-Dev-Site: ${SITE}" \
  "http://127.0.0.1:${PORT}/portal_api/v1/tenants/${TENANT}/sites/${SITE}/bigscreen/summary" \
| python3 -m json.tool

echo -e "\nTesting Display Token Auth..."
curl -s \
  -H "X-Display-Token: display_demo" \
  "http://127.0.0.1:${PORT}/portal_api/v1/tenants/${TENANT}/sites/${SITE}/bigscreen/summary" \
| python3 -m json.tool
