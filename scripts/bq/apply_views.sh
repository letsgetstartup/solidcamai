#!/usr/bin/env bash
set -euo pipefail

# Apply BigQuery Views for Big Screen Wallboard
# Usage: ./apply_views.sh [PROJECT_ID]

PROJECT_ID="${1:-solidcamal}"

echo "Applying erp_production_orders_latest view..."
bq query --use_legacy_sql=false < sql/views/erp_production_orders_latest.sql

echo "Applying site_orders_now view..."
bq query --use_legacy_sql=false < sql/views/site_orders_now.sql

echo "Done."
