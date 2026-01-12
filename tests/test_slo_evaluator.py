import unittest
import json
import os
import time
from scripts.observability.evaluate_slo import evaluate_slo

class TestSLOEvaluator(unittest.TestCase):
    def setUp(self):
        self.edge_metrics = ".tmp/test_edge.jsonl"
        self.cloud_metrics = ".tmp/test_cloud.jsonl"
        self.out_report = ".tmp/test_report.json"
        
        if os.path.exists(self.edge_metrics): os.remove(self.edge_metrics)
        if os.path.exists(self.cloud_metrics): os.remove(self.cloud_metrics)

    def test_slo_pass(self):
        # 1. Edge Metrics: Freshness PASS (last success 5s ago)
        with open(self.edge_metrics, "w") as f:
            f.write(json.dumps({"name": "edge.uplink.last_success_ts", "value": time.time() - 5, "type": "gauge"}) + "\n")
        
        # 2. Cloud Metrics: Latency PASS (all < 500ms)
        with open(self.cloud_metrics, "w") as f:
            f.write(json.dumps({"name": "cloud.ingest.latency_ms", "value": 150, "type": "histogram"}) + "\n")
            f.write(json.dumps({"name": "cloud.ingest.latency_ms", "value": 200, "type": "histogram"}) + "\n")
        
        success = evaluate_slo(self.edge_metrics, self.cloud_metrics, self.out_report)
        self.assertTrue(success)
        
        with open(self.out_report, "r") as f:
            r = json.load(f)
            self.assertEqual(r["overall_status"], "PASS")

    def test_slo_fail_freshness(self):
        # Edge Metrics: Freshness FAIL (last success 300s ago)
        with open(self.edge_metrics, "w") as f:
            f.write(json.dumps({"name": "edge.uplink.last_success_ts", "value": time.time() - 300, "type": "gauge"}) + "\n")
        
        evaluate_slo(self.edge_metrics, self.cloud_metrics, self.out_report)
        with open(self.out_report, "r") as f:
            r = json.load(f)
            self.assertEqual(r["slos"]["freshness"]["status"], "FAIL")
            self.assertEqual(r["overall_status"], "FAIL")

    def tearDown(self):
        for p in [self.edge_metrics, self.cloud_metrics, self.out_report]:
            if os.path.exists(p): os.remove(p)

if __name__ == "__main__":
    unittest.main()
