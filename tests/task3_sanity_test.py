import asyncio
import time
import os
import sys
import logging
from simco_agent.core.ingestor import Ingestor
from simco_agent.schemas import MachineInfo

# Configure minimal logging for the test
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("sanity_test")

async def run_sanity_test():
    print("\n" + "="*50)
    print("SIMCO AI: TASK 3 RELIABILITY SANITY TEST")
    print("="*50)

    # 1. Configuration
    # We use special IP addresses that our GenericProtocolDriver recognizes for simulation
    machines = [
        MachineInfo(ip="192.168.1.10", mac="HEALTHY_01", vendor="Generic", status="active"),
        MachineInfo(ip="TEST_HANG", mac="HANGING_01", vendor="Generic", status="active"),
        MachineInfo(ip="TEST_FAIL", mac="FAILING_01", vendor="Generic", status="active")
    ]

    ingestor = Ingestor()

    print(f"\n[Step 1] Executing Ingest Cycle with 3 machines...")
    print("    - 1 Healthy machine")
    print("    - 1 Hanging machine (Simulating 10s wait, 5s timeout)")
    print("    - 1 Failing machine (Simulating immediate crash)")
    
    start_time = time.time()
    
    # Run the cycle
    await ingestor.ingest_cycle(machines)
    
    elapsed = time.time() - start_time
    print(f"\n[Result] Ingest cycle completed in {elapsed:.2f} seconds.")

    # 2. Verification
    # A) Time Verification
    # Even though one machine hangs for 10s, the cycle should terminate around 5-6s due to timeout
    print(f"[Check] Bounded Execution Time...")
    if elapsed < 8:
        print("    ✅ PASS: Cycle was bounded by timeout (didn't wait full 10s).")
    else:
        print("    ❌ FAIL: Cycle took too long. Isolation failed.")
        sys.exit(1)

    # B) Data Integrity Verification
    # Check buffer file to see if HEALTHY_01 made it in
    from simco_agent.config import settings
    buffer_path = settings.BUFFER_FILE
    
    print(f"[Check] Data Integrity (Buffer Analysis)...")
    if os.path.exists(buffer_path):
        with open(buffer_path, "r") as f:
            lines = f.readlines()
            found_healthy = any("HEALTHY_01" in line for line in lines)
            
            if found_healthy:
                print(f"    ✅ PASS: Healthy machine data was buffered successfully.")
            else:
                print(f"    ❌ FAIL: Healthy machine data missing from buffer.")
                sys.exit(1)
    else:
        print("    ❌ FAIL: Buffer file not found.")
        sys.exit(1)

    print("\n" + "="*50)
    print("🏆 SANITY TEST PASSED: SYSTEM IS CRASH-PROOF!")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Ensure project root is in path
    sys.path.append(os.getcwd())
    asyncio.run(run_sanity_test())
