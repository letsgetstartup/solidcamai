import json
import time
import os
import threading

class Metrics:
    """Lightweight JSONL metrics emitter."""
    def __init__(self, path="metrics.jsonl"):
        self.path = path
        self._lock = threading.Lock()

    def _emit(self, name, value, type="gauge", labels=None):
        record = {
            "timestamp": time.time(),
            "name": name,
            "value": value,
            "type": type,
            "labels": labels or {}
        }
        with self._lock:
            with open(self.path, "a") as f:
                f.write(json.dumps(record) + "\n")

    def gauge(self, name, value, labels=None):
        self._emit(name, value, "gauge", labels)

    def counter(self, name, value=1, labels=None):
        self._emit(name, value, "counter", labels)

    def histogram(self, name, value, labels=None):
        self._emit(name, value, "histogram", labels)

# Global singleton for simple access
edge_metrics = Metrics(path="edge_metrics.jsonl")
cloud_metrics = Metrics(path="cloud_metrics.jsonl")
