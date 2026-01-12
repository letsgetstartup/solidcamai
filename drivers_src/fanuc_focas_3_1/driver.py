import time
import random

class FanucDriver:
    def __init__(self, host, port=8193):
        self.host = host
        self.port = port
        self.connected = False

    def connect(self):
        # Simulate connection delay
        time.sleep(0.1)
        self.connected = True
        return True

    def get_data(self):
        if not self.connected:
            raise ConnectionError("Not connected")
        return {
            "spindle_load": random.uniform(20.0, 95.0),
            "feed_rate": random.randint(500, 2000),
            "status": "RUNNING"
        }

    def close(self):
        self.connected = False
