CREATE OR REPLACE VIEW `simco_telemetry.erp_production_orders_latest` AS
SELECT
  tenant_id,
  JSON_VALUE(payload, '$.DocEntry') AS production_order_id,
  JSON_VALUE(payload, '$.ProductionOrder') AS production_order,
  JSON_VALUE(payload, '$.ItemNo') AS item,
  JSON_VALUE(payload, '$.Status') AS status,
  JSON_VALUE(payload, '$.DueDate') AS due_date,
  JSON_VALUE(payload, '$.UpdateDate') AS update_date,
  JSON_VALUE(payload, '$.ResourceCode') AS resource_code,
  JSON_VALUE(payload, '$.OperatorName') AS operator_name,
  source_updated_at,
  ingest_ts
FROM `simco_telemetry.erp_raw`
WHERE entity = "production_orders"
QUALIFY ROW_NUMBER() OVER (PARTITION BY tenant_id, JSON_VALUE(payload, '$.DocEntry') ORDER BY source_updated_at DESC, ingest_ts DESC) = 1;
