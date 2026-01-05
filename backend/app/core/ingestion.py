import os
import shutil
import uuid
from typing import List, Dict
from app.core.config import settings
import mimetypes

class FileIngestionService:
    def __init__(self):
        self.ingest_dir = settings.INGEST_DIR
        self.ready_dir = settings.READY_DIR

    def scan_ingest_folder(self) -> List[Dict]:
        """
        Scans the ingest folder for video files, moves them to 'ready',
        and returns a list of processed files.
        """
        processed_files = []
        if not os.path.exists(self.ingest_dir):
            return []

        for filename in os.listdir(self.ingest_dir):
            file_path = os.path.join(self.ingest_dir, filename)
            
            # Skip directories and non-files
            if not os.path.isfile(file_path):
                continue
                
            # Check for video mime type (basic check)
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type or not mime_type.startswith('video'):
                continue

            # Generate unique ID for the content
            content_id = str(uuid.uuid4())
            extension = os.path.splitext(filename)[1]
            new_filename = f"{content_id}{extension}"
            target_path = os.path.join(self.ready_dir, new_filename)

            try:
                # Move file to ready folder
                shutil.move(file_path, target_path)
                
                # In a real app, we would save this to the DB here
                file_info = {
                    "id": content_id,
                    "original_name": filename,
                    "path": target_path,
                    "status": "pending_review"
                }
                processed_files.append(file_info)
                print(f"Ingested: {filename} -> {new_filename}")
                
            except Exception as e:
                print(f"Error ingesting {filename}: {e}")

        return processed_files

    def list_ready_files(self) -> List[Dict]:
        """Lists files currently in the ready directory."""
        files = []
        if not os.path.exists(self.ready_dir):
            return []
            
        for filename in os.listdir(self.ready_dir):
            files.append({
                "filename": filename,
                "path": os.path.join(self.ready_dir, filename)
            })
        return files

ingestion_service = FileIngestionService()
