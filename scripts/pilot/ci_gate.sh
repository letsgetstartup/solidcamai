#!/bin/bash
# scripts/pilot/ci_gate.sh
set -e

echo "--- 🚀 STARTING CI QUALIFICATION GATE ---"

# 1. Run Unit Tests
echo "[1/3] Running Unit Tests..."
python3 -m unittest discover tests -p "test_*.py" -q

# 2. Run Pilot Suite (Compressed Outage)
echo "[2/3] Running Pilot Qualification (Time-Compressed Outage)..."
python3 scripts/pilot/run_pilot_suite.py \
  --machines 10 \
  --outage_sim_minutes 30 \
  --outage_time_compress_to_seconds 5 \
  --report_path reports/pilot_ci_report.json

# 3. Certify
echo "[3/3] Generating Acceptance Certificate..."
python3 -m simco_agent.core.qa_certify --report reports/pilot_ci_report.json

echo "--- ✅ CI GATE PASSED ---"
