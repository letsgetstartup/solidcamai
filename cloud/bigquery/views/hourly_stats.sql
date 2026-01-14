CREATE OR REPLACE VIEW `simco_telemetry.hourly_machine_stats` AS
WITH base AS (
  SELECT
    tenant_id,
    site_id,
    machine_id,
    TIMESTAMP_TRUNC(timestamp, HOUR) as hour_bucket,
    status,
    timestamp,
    LEAD(timestamp) OVER (PARTITION BY machine_id ORDER BY timestamp) as next_ts
  FROM
    `simco_telemetry.raw_telemetry`
),
durations AS (
  SELECT
    tenant_id,
    site_id,
    machine_id,
    hour_bucket,
    status,
    TIMESTAMP_DIFF(COALESCE(next_ts, TIMESTAMP_ADD(timestamp, INTERVAL 1 MINUTE)), timestamp, SECOND) as duration_seconds
  FROM
    base
  WHERE
    timestamp IS NOT NULL
)
SELECT
  tenant_id,
  site_id,
  machine_id,
  hour_bucket,
  SUM(CASE WHEN status IN ('ACTIVE', 'RUNNING') THEN duration_seconds ELSE 0 END) / 60.0 as minutes_active,
  SUM(CASE WHEN status IN ('IDLE', 'READY') THEN duration_seconds ELSE 0 END) / 60.0 as minutes_idle,
  SUM(CASE WHEN status IN ('ALARM', 'FAULT', 'ERROR') THEN duration_seconds ELSE 0 END) / 60.0 as minutes_alarm,
  SUM(CASE WHEN status IN ('STOPPED', 'OFFLINE') THEN duration_seconds ELSE 0 END) / 60.0 as minutes_stopped
FROM
  durations
GROUP BY
  1, 2, 3, 4
