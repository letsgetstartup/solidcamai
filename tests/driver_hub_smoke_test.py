import json
import hashlib
import os
import subprocess
import sys

def test_manifest_generation():
    print("--- Testing Manifest Generation ---")
    cmd = [
        sys.executable, "-m", "tools.driver_hub.generate_manifest",
        "--drivers-dir", "driver_hub/drivers",
        "--base-url", "http://localhost:8088/drivers",
        "--out", "driver_hub/manifest.json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Manifest generation failed: {result.stderr}"
    print("OK: Manifest generated.")

def test_manifest_readability():
    print("--- Testing Manifest Readability ---")
    with open("driver_hub/manifest.json", "r") as f:
        m = json.load(f)
    assert "drivers" in m and len(m["drivers"]) >= 1, "manifest must include at least 1 driver"
    print(f"OK: Found {len(m['drivers'])} drivers.")
    return m

def test_sha256_integrity(m):
    print("--- Testing SHA-256 Integrity ---")
    d = m["drivers"][0]
    artifact = d.get("artifact_path") or f"driver_hub/drivers/{d['driver_id']}/{d['version']}/driver.zip"
    
    assert os.path.exists(artifact), f"Artifact not found: {artifact}"
    
    with open(artifact, "rb") as f:
        b = f.read()
    
    h = hashlib.sha256(b).hexdigest()
    print(f"Artifact: {artifact}")
    print(f"Manifest SHA256: {d['sha256']}")
    print(f"Computed SHA256: {h}")
    
    assert h == d["sha256"], "SHA256 mismatch"
    print("OK: SHA256 matches.")

def test_determinism():
    print("--- Testing Determinism ---")
    subprocess.run([sys.executable, "-m", "tools.driver_hub.generate_manifest", "--drivers-dir", "driver_hub/drivers", "--base-url", "http://localhost:8088/drivers", "--out", "driver_hub/manifest_1.json"], check=True)
    subprocess.run([sys.executable, "-m", "tools.driver_hub.generate_manifest", "--drivers-dir", "driver_hub/drivers", "--base-url", "http://localhost:8088/drivers", "--out", "driver_hub/manifest_2.json"], check=True)
    
    with open("driver_hub/manifest_1.json") as f1, open("driver_hub/manifest_2.json") as f2:
        m1 = json.load(f1)
        m2 = json.load(f2)
    
    m1.pop("generated_at")
    m2.pop("generated_at")
    
    assert m1 == m2, "Manifest generation is not deterministic"
    print("OK: Manifest generation is deterministic.")

if __name__ == "__main__":
    try:
        test_manifest_generation()
        m = test_manifest_readability()
        test_sha256_integrity(m)
        test_determinism()
        print("\n🏆 ALL DRIVER HUB SMOKE TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ SMOKE TEST FAILED: {e}")
        sys.exit(1)
