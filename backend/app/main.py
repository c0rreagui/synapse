from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Auto Content Empire API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os
from .api.endpoints import content, ingestion, profiles, logs, queue, videos
from .api import debug_router

# Mount static for debugging
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["logs"])
app.include_router(queue.router, prefix="/api/v1/queue", tags=["queue"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(debug_router.router, prefix="/api/v1", tags=["debug"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Synapse Factory"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
