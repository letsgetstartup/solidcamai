#!/bin/bash
# scripts/security_checks.sh
set -e

echo "--- 🛡️ SIMCO AI SECURITY GATES ---"

echo "[1/3] Dependency Scanning (pip-audit)..."
pip-audit --ignore-vuln GHSA-w596-868m-8v6f # Example ignore if needed

echo "[2/3] Static Analysis (bandit)..."
bandit -r simco_agent -ll -iii

echo "[3/3] SBOM Generation (cyclonedx)..."
cyclonedx-py requirements ./requirements.txt --output-format json --output-file ./sbom_edge.json
cyclonedx-py requirements ./functions/requirements.txt --output-format json --output-file ./sbom_cloud.json

echo "--- ✅ ALL SECURITY GATES PASSED ---"
