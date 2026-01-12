import asyncio
import time
import os
import sys
import sqlite3
from simco_agent.core.buffer_manager import BufferManager
from simco_agent.core.uplink_worker import UplinkWorker
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

def run_task4_sanity():
    print("\n" + "="*50)
    print("SIMCO AI: TASK 4 STORE-AND-FORWARD SANITY TEST")
    print("="*50)

    db_path = ".tmp_sanity_task4.db"
    if os.path.exists(db_path): os.remove(db_path)
    
    # 1. Start Stub Server that fails 2 times
    state = {"count": 0}
    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            state["count"] += 1
            if state["count"] <= 2:
                self.send_response(500); self.end_headers()
            else:
                self.send_response(200); self.end_headers()
        def log_message(self, *args): return

    srv = HTTPServer(("127.0.0.1", 8100), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    # 2. Enqueue Data
    os.environ["SIMCO_INGEST_URL"] = "http://127.0.0.1:8100"
    bm = BufferManager(db_path)
    print("Enqueuing 10 records...")
    for i in range(10):
        bm.enqueue({"id": i, "val": "sanity"})
    
    print(f"Initial Queue Count: {bm.stats()['queued_count']}")

    # 3. Run Worker
    async def run():
        w = UplinkWorker(buffer_manager=bm)
        w.interval = 0.5
        task = asyncio.create_task(w.run())
        print("Waiting for worker recovery and drain...")
        await asyncio.sleep(10)
        w.stop()
        task.cancel()

    asyncio.run(run())

    # 4. Final Result
    final_stats = bm.stats()
    print(f"Final Queue Count: {final_stats['queued_count']}")
    
    if final_stats['queued_count'] == 0:
        print("\n🏆 SANITY TEST PASSED: STORE-AND-FORWARD IS RELIABLE!")
    else:
        print("\n❌ SANITY TEST FAILED: BUFFER DID NOT DRAIN")
        sys.exit(1)
    
    srv.shutdown()
    if os.path.exists(db_path): os.remove(db_path)

if __name__ == "__main__":
    run_task4_sanity()
