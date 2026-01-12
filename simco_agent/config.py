from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "SIMCO AI Edge Gateway"
    VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Network Scanning
    SCAN_SUBNET: str = "192.168.1.0/24"
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

    class Config:
        env_prefix = "SIMCO_"

settings = Settings()
