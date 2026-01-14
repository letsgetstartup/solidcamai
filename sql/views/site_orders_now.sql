CREATE OR REPLACE VIEW `simco_telemetry.site_orders_now` AS
SELECT
  m.tenant_id,
  m.site_id,
  m.machine_id,
  m.erp_system,
  m.erp_resource_code AS resource_code,
  o.production_order,
  o.item,
  o.status,
  o.due_date,
  o.operator_name,
  (SAFE_CAST(o.due_date AS DATE) < CURRENT_DATE()) AS late
FROM `simco_telemetry.erp_machine_map` m
LEFT JOIN `simco_telemetry.erp_production_orders_latest` o
  ON o.tenant_id = m.tenant_id AND o.resource_code = m.erp_resource_code
-- In many shops resource mapping is indirect; if SAP provides a resource/workcenter field, join it here.
;
