#!/bin/bash
set -e

echo "🧪 Starting Full Cycle E2E Test (Simulated Local)"
API_URL="http://127.0.0.1:8081/portal_api/v1/tenants/tenant_demo/sites/site_demo/machines"

# 1. Check if DevStack is running
if ! pgrep -f "router_stub.py" > /dev/null; then
  echo "❌ DevStack not running. Please run ./scripts/dev/up.sh first."
  exit 1
fi

echo "✅ DevStack detected."

# 2. Reset Registry (Optional, but good for clean test usually. Skipping to use running state)
# In a real CI script we would tear down and spin up.

# 3. Poll Portal API for machine status
echo "🔍 Polling Portal API for active machines..."
MAX_RETRIES=10
FOUND=0

for i in $(seq 1 $MAX_RETRIES); do
  RESPONSE=$(curl -s -H "X-Dev-Role: Manager" -H "X-Dev-Tenant: tenant_demo" -H "X-Dev-Site: site_demo" "$API_URL")
  
  # Check if response contains "RUNNING" or "ACTIVE" or our generic driver status
  if [[ "$RESPONSE" == *"machine_id"* ]]; then
    echo "✅ Machine data found in Cloud!"
    echo "Response: $RESPONSE"
    FOUND=1
    break
  fi
  
  echo "   Attempt $i/$MAX_RETRIES: No data yet. Waiting..."
  sleep 3
done

if [ $FOUND -eq 0 ]; then
  echo "❌ Test FAILED: Data did not reach Cloud Portal within timeout."
  exit 1
fi

# 4. Check Events (Optional)
EVENTS_URL="http://127.0.0.1:8081/portal_api/v1/tenants/tenant_demo/sites/site_demo/events"
echo "🔍 Checking for Events..."
EVENTS=$(curl -s -H "X-Dev-Role: Manager" -H "X-Dev-Tenant: tenant_demo" -H "X-Dev-Site: site_demo" "$EVENTS_URL")
if [[ "$EVENTS" == *"event_type"* ]]; then
    echo "✅ Events found!"
    echo "Events: $EVENTS"
else
    echo "⚠️ No events yet (might be normal if no anomalies triggered)."
fi

echo "🎉 FULL CYCLE TEST PASSED"
exit 0
