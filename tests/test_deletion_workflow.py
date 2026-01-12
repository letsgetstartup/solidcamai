import unittest
from cloud.data_lifecycle.process_deletions import process_deletions
import io
from contextlib import redirect_stdout

class TestDeletionWorkflow(unittest.TestCase):
    def test_dry_run_deletion_plan(self):
        f = io.StringIO()
        with redirect_stdout(f):
            process_deletions("SIMCO_DATASET", dry_run=True)
        
        output = f.getvalue()
        # Ensure machine scope generated
        self.assertIn("DELETE FROM `SIMCO_DATASET.*` WHERE tenant_id = 'tenant_demo' AND machine_id = 'haas_old';", output)
        # Ensure tenant scope generated
        self.assertIn("DELETE FROM `SIMCO_DATASET.*` WHERE tenant_id = 'tenant_test';", output)

if __name__ == "__main__":
    unittest.main()
