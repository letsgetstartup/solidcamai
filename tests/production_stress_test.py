import asyncio
import aiohttp
import time
import statistics
import json

BASE_URL = "https://solidcam-f58bc.web.app"
ENDPOINTS = {
    "pair_init": f"{BASE_URL}/pair_init",
}

CONCURRENT_REQUESTS = 1000
TIMEOUT = 30

async def perform_request(session, url, data):
    start = time.time()
    try:
        async with session.post(url, json=data, timeout=TIMEOUT) as response:
            status = response.status
            body = await response.text()
            latency = (time.time() - start) * 1000
            return {"status": status, "latency": latency, "success": status == 200}
    except Exception as e:
        return {"status": "error", "latency": (time.time() - start) * 1000, "success": False, "error": str(e)}

async def run_stress_test():
    print(f"🚀 Starting Stress Test: {CONCURRENT_REQUESTS} concurrent requests to /pair_init")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(CONCURRENT_REQUESTS):
            data = {"fingerprint": f"stress-test-device-{i}"}
            tasks.append(perform_request(session, ENDPOINTS["pair_init"], data))
        
        results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r["success"])
    latencies = [r["latency"] for r in results if r["status"] == 200]
    errors = [r for r in results if not r["success"]]
    
    print("\n--- Stress Test Results ---")
    print(f"Total Requests: {CONCURRENT_REQUESTS}")
    print(f"Successes: {success_count} ({success_count/CONCURRENT_REQUESTS*100:.2f}%)")
    print(f"Failures: {len(errors)}")
    
    if latencies:
        print(f"Avg Latency: {statistics.mean(latencies):.2f}ms")
        print(f"P95 Latency: {statistics.quantiles(latencies, n=20)[18]:.2f}ms")
        print(f"Max Latency: {max(latencies):.2f}ms")
    
    if errors:
        print("\n--- Error Breakdown ---")
        error_summary = {}
        for e in errors:
            key = f"Status {e.get('status')} / {e.get('error', 'No Error Msg')}"
            error_summary[key] = error_summary.get(key, 0) + 1
        for msg, count in error_summary.items():
            print(f"{msg}: {count}")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
