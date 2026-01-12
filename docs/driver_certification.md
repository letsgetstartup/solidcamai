# Driver Certification Program (v3.1)

All SIMCO AI drivers must pass the formal certification pipeline before they can be promoted to the `prod` release channel.

## 1. Local Development
Drivers are developed in `drivers_src/<driver_id>/`.
Each driver folder must contain:
- `driver.py`: Core logic.
- `metadata.yaml`: Compatibility matrix data.
- `requirements.txt`: Individual dependencies.
- `tests/`: Unit tests.

## 2. Certification Process
Run the certification suite locally or in CI:
```bash
python -m drivers_testkit.certify --driver_id <id> --version <v>
```
Gates enforced:
- **Unit Tests**: Mandatory pass.
- **Security Scan**: Analysis of `requirements.txt` for known vulnerabilities.
- **Protocol Simulation**: Verification against a simulated controller (where available).

## 3. Build & Publish
Once certified (status=PASS), artifacts are built:
```bash
python scripts/drivers/build_driver_artifact.py --driver_id <id> --version <v>
```

## 4. Promotion Gate
The `build_release.sh` script now automatically checks for a valid `cert_report.json` before allowing a driver to be listed in the production `manifest.json`.
