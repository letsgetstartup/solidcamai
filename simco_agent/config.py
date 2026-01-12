from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "SIMCO AI Edge Gateway"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Network Scanning
    SCAN_SUBNET: str = "127.0.0.1/32"
    SCAN_INTERVAL_SECONDS: int = 60

    # Data Buffering
    BUFFER_FILE: str = "buffer.jsonl"
    MACHINE_REGISTRY_FILE: str = "machine_registry.json"
    
    # Cloud Connectivity
    GCP_PROJECT_ID: str = "simco-ai-prod"
    BQ_DATASET: str = "simco_telemetry"
    BQ_TABLE: str = "raw_telemetry"
    
    # Anomaly Thresholds
    SPINDLE_LOAD_THRESHOLD: float = 90.0

    # Driver Hub & Sync
    DRIVERS_CACHE_DIR: str = "drivers_cache"
    DRIVERS_ACTIVE_DIR: str = "drivers_active"
    DRIVERS_BACKUP_DIR: str = "drivers_backup"
    DRIVER_HUB_MANIFEST_URL: str = "http://localhost:8088/manifest.json"

    # Store-and-Forward Buffer (Task 4)
    BUFFER_DB: str = "buffer.db"
    
    # Reliable Uplink (Task 4)
    INGEST_URL: str = "https://your-cloud-function.cloudfunctions.net/ingest"
    UPLOAD_BATCH_SIZE: int = 100
    UPLOAD_INTERVAL_SECONDS: int = 5
    UPLOAD_TIMEOUT_SECONDS: int = 10

    # Fleet Management (Task 6)
    MGMT_BASE_URL: str = "http://127.0.0.1:8090"
    BOOTSTRAP_TOKEN: str = "devtoken"
    DEVICE_STATE_FILE: str = "device_state.json"
    TENANT_ID: str = "pending"
    SITE_ID: str = "pending"
    HEARTBEAT_INTERVAL_SECONDS: int = 30
    CONFIG_POLL_INTERVAL_SECONDS: int = 60

    # Security Hardening (Task 7)
    DEVICE_CERT_PATH: Optional[str] = None
    DEVICE_KEY_PATH: Optional[str] = None
    CA_CERT_PATH: Optional[str] = None
    DRIVER_PUBKEY_PATH: str = "keys/driver_verify.pub"

    class Config:
        env_prefix = "SIMCO_"

settings = Settings()
