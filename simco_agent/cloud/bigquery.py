import logging
import json
from typing import List, Dict, Any
from google.cloud import bigquery
from simco_agent.drivers.common.models import TelemetryPoint

logger = logging.getLogger(__name__)

class BigQueryClient:
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = None
        
        # In a real app, we'd auth here
        try:
             # This will fail without credentials, but we wrap it
             # For mocking, we assume client is injected or patched
             self.client = bigquery.Client(project=project_id)
             self.table_ref = self.client.dataset(dataset_id).table(table_id)
        except Exception as e:
            logger.warning(f"Failed to init BQ client (expected in local env): {e}")

    def stream_rows(self, rows: List[Dict[str, Any]]) -> bool:
        if not self.client:
            logger.error("BQ Client not initialized")
            return False

        try:
            errors = self.client.insert_rows_json(self.table_ref, rows)
            if errors:
                logger.error(f"BQ Insert Errors: {errors}")
                return False
            return True
        except Exception as e:
            logger.error(f"BQ Stream Error: {e}")
            return False
