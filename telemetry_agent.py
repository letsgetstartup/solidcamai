import time
import json
import logging
import nmap
import schedule
from datetime import datetime
import os

# --- Configuration ---
SCAN_INTERVAL_SECONDS = 60
BUFFER_FILE = "buffer.jsonl"
MACHINE_REGISTRY_FILE = "machine_registry.json"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SIMCO_AI_AGENT")

# --- Agent A: Reconnaissance (Network Architect) ---
class ReconAgent:
    def __init__(self):
        self.nm = nmap.PortScanner()
        self.registry = {}

    def scan_network(self, subnet="192.168.1.0/24"):
        logger.info(f"Agent A: Scanning subnet {subnet}...")
        try:
            # Scanning for common CNC ports: 8193 (Fanuc), 4840 (OPC UA), 502 (Modbus), 7878 (MTConnect)
            self.nm.scan(hosts=subnet, arguments='-p 8193,4840,502,7878 --open')
            
            new_hosts_found = 0
            for host in self.nm.all_hosts():
                if host not in self.registry:
                    vendor = self._identify_vendor(host)
                    self.registry[host] = {
                        "ip": host,
                        "mac": self.nm[host]['addresses'].get('mac', 'Unknown'),
                        "vendor": vendor,
                        "status": "discovered",
                        "discovered_at": datetime.now().isoformat()
                    }
                    new_hosts_found += 1
                    logger.info(f"Agent A: Discovered new machine at {host} ({vendor})")
            
            if new_hosts_found > 0:
                self._save_registry()
                
        except Exception as e:
            logger.error(f"Agent A Scan Error: {e}")

    def _identify_vendor(self, host):
        # Simple heuristic based on open ports
        ports = self.nm[host].get('tcp', {})
        if 8193 in ports: return "Fanuc"
        if 4840 in ports: return "OPC_UA"
        if 502 in ports: return "Modbus_Haas"
        if 7878 in ports: return "MTConnect"
        return "Unknown_CNC"

    def _save_registry(self):
        with open(MACHINE_REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)
        logger.info("Agent A: Registry updated.")

# --- Agent B: Ingestion (Driver Manager) ---
class DataIngestionAgent:
    def __init__(self):
        self.buffer_file = BUFFER_FILE

    def collect_telemetry(self, registry):
        logger.info("Agent B: Collecting telemetry from registered machines...")
        # In a real scenario, this would spawn drivers based on registry['vendor']
        # Here we simulate data collection
        
        batch_data = []
        for ip, info in registry.items():
            if info.get('status') == 'discovered':
                # Simulation of reading data
                data_point = {
                    "machine_id": info.get('mac', ip),
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "ACTIVE",
                    "spindle_load": self._simulate_spindle_load(),
                    "program_name": "O1001_BRACKET_V2"
                }
                
                # Anomaly Detection (Edge AI)
                if data_point['spindle_load'] > 90:
                    data_point['anomaly'] = True
                    logger.warning(f"Agent B: Anomaly detected on {ip} - Spindle Load: {data_point['spindle_load']}%")
                
                batch_data.append(data_point)
        
        if batch_data:
            self.buffer_data(batch_data)

    def _simulate_spindle_load(self):
        # Simulating a value between 0 and 100
        import random
        return random.randint(20, 95)

    def buffer_data(self, data):
        try:
            with open(self.buffer_file, 'a') as f:
                for entry in data:
                    f.write(json.dumps(entry) + "\n")
            logger.info(f"Agent B: Buffered {len(data)} telemetry records locally.")
        except Exception as e:
            logger.error(f"Agent B Buffer Error: {e}")

# --- Orchestrator ---
def job():
    # Load registry
    try:
        if os.path.exists(MACHINE_REGISTRY_FILE):
            with open(MACHINE_REGISTRY_FILE, 'r') as f:
                registry = json.load(f)
        else:
            registry = {}
    except Exception:
        registry = {}

    # Agent A Run
    recon.scan_network()
    
    # Reload registry after scan
    try:
        if os.path.exists(MACHINE_REGISTRY_FILE):
            with open(MACHINE_REGISTRY_FILE, 'r') as f:
                registry = json.load(f)
    except:
        pass

    # Agent B Run
    ingestion.collect_telemetry(registry)

if __name__ == "__main__":
    logger.info("SIMCO AI Edge Gateway Starting...")
    
    recon = ReconAgent()
    ingestion = DataIngestionAgent()
    
    # Initial run
    job()
    
    # Schedule
    schedule.every(SCAN_INTERVAL_SECONDS).seconds.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
