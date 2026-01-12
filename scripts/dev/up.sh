#!/bin/bash
# SIMCO AI v3.1 DevStack Up

echo "🚀 Starting SIMCO AI v3.1 Local DevStack..."

# 1. Start Support Services
echo "  [1/4] Starting Management Stub (8090)..."
PYTHONPATH=. ./venv/bin/python3 functions/mgmt_stub.py > mgmt.log 2>&1 &
MGMT_PID=$!

echo "  [2/4] Starting Unified Cloud Router (Ingest + Portal API) (8081)..."
PYTHONPATH=. ./venv/bin/python3 scripts/dev/router_stub.py > router.log 2>&1 &
ROUTER_PID=$!

echo "  [3/4] Starting UI Server (5173)..."
./venv/bin/python3 -m http.server 5173 --directory web > ui.log 2>&1 &
UI_PID=$!

# 2. Wait for stubs to be ready
sleep 5

# 3. Start Edge Agent
echo "  [4/4] Starting Edge Agent..."
export SIMCO_MGMT_BASE_URL="http://127.0.0.1:8090"
# Ingest is at root or /ingest in the router
export SIMCO_INGEST_URL="http://127.0.0.1:8081/ingest"
export SIMCO_UPLOAD_INTERVAL_SECONDS=5
export SIMCO_SCAN_INTERVAL_SECONDS=10

PYTHONPATH=. ./venv/bin/python3 -m simco_agent > agent.log 2>&1 &
AGENT_PID=$!

echo "✅ DevStack is UP!"
echo "   UI: http://127.0.0.1:5173/dashboard.html?dev=1"
echo "   Management: http://127.0.0.1:8090"
echo "   Cloud Router: http://127.0.0.1:8081"
echo ""
echo "PIDs: Management($MGMT_PID), Router($ROUTER_PID), UI($UI_PID), Agent($AGENT_PID)"

# Store PIDS for shutdown
echo "$MGMT_PID $ROUTER_PID $UI_PID $AGENT_PID" > .devstack_pids
