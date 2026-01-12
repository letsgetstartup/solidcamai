import asyncio
import logging
import os
import glob
import json
import time
from typing import List, Dict, Any
from ..config import settings
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger("simco_agent.cloud")

class MockBigQueryClient:
    """Mock Client for development usage without GCP credentials."""
    def __init__(self, project: str):
        self.project = project
        logger.info(f"Initialized Mock BigQuery Client for project {project}")

    def insert_rows_json(self, table_id: str, rows: List[Dict[str, Any]]) -> List[Any]:
        # Simulate network latency
        time.sleep(0.5)
        logger.info(f"MOCK BQ: Inserted {len(rows)} rows into {table_id}")
        # Return empty list means no errors
        return []

class CloudUploader:
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.dataset_id = settings.BQ_DATASET
        self.table_id = f"{self.project_id}.{self.dataset_id}.{settings.BQ_TABLE}"
        self.buffer_file = settings.BUFFER_FILE
        self.upload_interval = 10 # seconds based on plan/task description, or keep it responsive loop

        # Initialize Client
        try:
             # In production, this would use ADC. For dev, we fallback to Mock if auth fails or requested.
             # Checking a fictious env var to force mock for safety if needed, or catch exception
             self.client = bigquery.Client(project=self.project_id)
             logger.info("Connected to Real BigQuery Client")
        except Exception as e:
             logger.warning(f"Failed to connect to BigQuery ({e}). Using Mock Client.")
             self.client = MockBigQueryClient(project=self.project_id)

    async def run_loop(self):
        """Continuous loop to monitor buffer and upload."""
        logger.info("Starting CloudUploader loop...")
        while True:
            await self.process_buffers()
            await asyncio.sleep(self.upload_interval)

    async def process_buffers(self):
        """Rotates current buffer and processes all queued batch files."""
        # 1. Rotate current buffer if it exists and has content
        self._rotate_buffer()

        # 2. Find all batch files
        batch_files = glob.glob(f"{self.buffer_file}.*")
        
        for batch_file in batch_files:
            await self._upload_batch(batch_file)

    def _rotate_buffer(self):
        """Renames buffer.jsonl to buffer.jsonl.{timestamp} to atomize the batch."""
        if os.path.exists(self.buffer_file) and os.path.getsize(self.buffer_file) > 0:
            timestamp = int(time.time() * 1000)
            new_name = f"{self.buffer_file}.{timestamp}"
            try:
                os.rename(self.buffer_file, new_name)
                logger.debug(f"Rotated buffer to {new_name}")
            except OSError as e:
                logger.error(f"Error rotating buffer: {e}")

    async def _upload_batch(self, filepath: str):
        """Reads a batch file, uploads to BQ, and deletes on success."""
        rows = []
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        rows.append(json.loads(line))
        except Exception as e:
            logger.error(f"Corrupt batch file {filepath}: {e}")
            # Move to quarantine or just delete? For now, we rename to .corrupt to avoid blocking
            os.rename(filepath, filepath + ".corrupt")
            return

        if not rows:
            os.remove(filepath)
            return

        # Upload
        try:
            # Run blocking BQ call in thread executor
            loop = asyncio.get_running_loop()
            errors = await loop.run_in_executor(
                None, 
                lambda: self.client.insert_rows_json(self.table_id, rows)
            )

            if not errors:
                logger.info(f"Successfully uploaded {len(rows)} records from {filepath}")
                os.remove(filepath)
            else:
                logger.error(f"BigQuery Insert Errors: {errors}")
                # Keep file to retry later
        except Exception as e:
            logger.error(f"Upload failed for {filepath}: {e}")
            # Keep file, next cycle will pick it up
