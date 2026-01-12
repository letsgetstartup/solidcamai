# SIMCO AI | Driver Hub Specification

The Driver Hub is the central authority for CNC machine drivers. It enables the Edge Ingestor (Agent B) to download and load drivers dynamically based on discovered hardware.

## Layout Structure
```text
driver_hub/
├── manifest.json
└── drivers/
    └── <driver_id>/
        └── <version>/
            └── driver.zip
```

## Manifest Schema
- `manifest_version`: Version of the schema (currently 1.0.0).
- `generated_at`: UTC timestamp.
- `drivers`: Array of driver objects.
    - `driver_id`: Unique identifier (e.g., "fanuc").
    - `version`: Semantic version.
    - `channel`: "prod" or "staging".
    - `sha256`: Checksum of the `driver.zip`.
    - `url`: Download URL.
    - `entrypoint`: Class locator (e.g., `driver:FanucDriver`).
    - `supported_vendors`: List of hardware vendors supported.
    - `python`: Python version requirement.

## Adding a New Driver
1. Create a directory: `driver_hub/drivers/<id>/<version>/`.
2. Place your driver code and a `driver.py` entrypoint.
3. Zip the contents as `driver.zip`.
4. Run the manifest generator:
```bash
python -m tools.driver_hub.generate_manifest --drivers-dir driver_hub/drivers --base-url http://localhost:8088/drivers --out driver_hub/manifest.json
```

## Local Development Hub
To test locally, you can serve the `driver_hub` directory:
```bash
cd driver_hub && python3 -m http.server 8088
```
