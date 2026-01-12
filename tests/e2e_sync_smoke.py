import os
import subprocess
import time
import requests
import json
import shutil
from simco_agent.drivers.factory import DriverFactory

def run_smoke_test():
    print("--- STARTING E2E SYNC SMOKE TEST ---")
    
    # 1. Setup paths
    tmp_root = os.path.abspath(".tmp_smoke")
    shutil.rmtree(tmp_root, ignore_errors=True)
    os.makedirs(tmp_root)
    
    cache_dir = os.path.join(tmp_root, "cache")
    active_dir = os.path.join(tmp_root, "active")
    backup_dir = os.path.join(tmp_root, "backup")
    
    # 2. Start local hub server
    print("Starting local hub server...")
    hub_proc = subprocess.Popen(["python3", "-m", "http.server", "8088", "--directory", "driver_hub"])
    time.sleep(2) # Wait for server to start

    try:
        # 3. Configure ENV
        env = os.environ.copy()
        env["SIMCO_DRIVER_HUB_MANIFEST_URL"] = "http://localhost:8088/manifest.json"
        env["SIMCO_DRIVERS_CACHE_DIR"] = cache_dir
        env["SIMCO_DRIVERS_ACTIVE_DIR"] = active_dir
        env["SIMCO_DRIVERS_BACKUP_DIR"] = backup_dir
        env["PYTHONPATH"] = os.getcwd()

        # 4. Run Sync CLI
        print("Running sync CLI...")
        subprocess.run([sys.executable, "-m", "simco_agent.sync_drivers"], env=env, check=True)

        # 5. Verify layout
        print(f"Verifying ACTIVE_DIR: {active_dir}")
        found_active = False
        for root, dirs, files in os.walk(active_dir):
            if "metadata.json" in files:
                print(f"Found active driver in {root}")
                found_active = True
                break
        assert found_active, "No active driver found after sync"

        # 6. Test Dynamic Import via Factory
        print("Testing Dynamic Import via DriverFactory...")
        # We need to monkeypatch settings or use the environment in the factory
        # Since factory uses global settings object, let's update it directly for this test
        from simco_agent.config import settings
        settings.DRIVERS_ACTIVE_DIR = active_dir
        
        d = DriverFactory.get_driver("Fanuc", "192.168.1.10")
        print(f"Instance: {type(d)}")
        assert "FanucDriver" in str(type(d)), f"Expected FanucDriver, got {type(d)}"
        
        print("Driver IP:", getattr(d, "ip", None))
        
        print("\n🏆 E2E SYNC SMOKE TEST PASSED!")
        
    finally:
        print("Shutting down hub server...")
        hub_proc.terminate()
        hub_proc.wait()

import sys
if __name__ == "__main__":
    run_smoke_test()
