class ProtocolSimulator:
    """Abstract base for simulating industrial protocols (FOCAS, Modbus, etc)."""
    def __init__(self, port):
        self.port = port
        self.running = False

    def start(self):
        self.running = True
        print(f"Simulator started on port {self.port}")

    def stop(self):
        self.running = False
        print("Simulator stopped")

    def handle_request(self, data):
        raise NotImplementedError
