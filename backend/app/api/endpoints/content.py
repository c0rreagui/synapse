from fastapi import APIRouter, HTTPException
from typing import List
from ...core.ingestion import ingestion_service

router = APIRouter()

@router.post("/scan", response_model=List[dict])
async def scan_ingest_folder():
    """Triggers a scan of the ingest folder."""
    try:
        files = ingestion_service.scan_ingest_folder()
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ready", response_model=List[dict])
async def list_ready_content():
    """Lists content ready for distribution."""
    return ingestion_service.list_ready_files()
