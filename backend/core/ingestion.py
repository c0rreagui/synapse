import os
import glob
from typing import List, Dict

class IngestionService:
    def __init__(self):
        # Base dir is Synapse/
        # This file is in Synapse/backend/core/ingestion.py
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.inputs_dir = os.path.join(self.base_dir, "data", "inputs")
        self.pending_dir = os.path.join(self.base_dir, "data", "pending")
        self.done_dir = os.path.join(self.base_dir, "data", "done")
        
        os.makedirs(self.inputs_dir, exist_ok=True)
        os.makedirs(self.pending_dir, exist_ok=True)
        os.makedirs(self.done_dir, exist_ok=True)

    def scan_ingest_folder(self) -> List[Dict]:
        """Scans for new files in inputs/pending folder."""
        files = []
        # Check Pending
        if os.path.exists(self.pending_dir):
            for f in os.listdir(self.pending_dir):
                if f.endswith(('.mp4', '.mov', '.avi')):
                    files.append({"filename": f, "path": os.path.join(self.pending_dir, f), "status": "pending"})
        return files

    def list_ready_files(self) -> List[Dict]:
        """Lists files that are done/ready."""
        files = []
        if os.path.exists(self.done_dir):
             for f in os.listdir(self.done_dir):
                if f.endswith('.mp4'):
                     files.append({"filename": f, "path": os.path.join(self.done_dir, f), "status": "completed"})
        return files

ingestion_service = IngestionService()
