import unittest
from cloud.data_lifecycle.enforce_retention import enforce_retention
import io
from contextlib import redirect_stdout

class TestRetentionEnforcer(unittest.TestCase):
    def test_dry_run_sql_generation(self):
        f = io.StringIO()
        with redirect_stdout(f):
            enforce_retention("SIMCO_DATASET", "cloud/data_lifecycle/retention_plans.yaml", dry_run=True)
        
        output = f.getvalue()
        self.assertIn("ALTER TABLE `SIMCO_DATASET.raw_telemetry` SET OPTIONS (partition_expiration_days = 90);", output)
        self.assertIn("ALTER TABLE `SIMCO_DATASET.daily_rollups` SET OPTIONS (partition_expiration_days = 1095);", output)

if __name__ == "__main__":
    unittest.main()
