import asyncio
import sys
import os

# 🛡️ GLOBAL UTF-8 ENFORCEMENT (Fixes Windows Console Crashing Agent)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not force UTF-8: {e}")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Auto Content Empire API")
# Force Reload Trigger (Final Config)

@app.on_event("startup")
async def startup_event():
    from core.status_manager import status_manager
    from core.logger import logger
    from .api.websocket import notify_pipeline_update, notify_new_log
    
    # Registra o callback para enviar atualizações via WebSocket
    status_manager.set_async_callback(notify_pipeline_update)
    logger.set_async_callback(notify_new_log)
    print("SYSTEM: Real-time updates handler registered.")

    # Start Background Workers
    try:
        from core.factory_watcher import start_watcher
        from core.queue_worker import worker_loop
        
        # Start Factory Watcher (Watchdog)
        app.state.watcher_observer = await start_watcher()
        
        # Start Queue Worker (Async Loop)
        app.state.queue_worker_task = asyncio.create_task(worker_loop())
        
        # Start Oracle Automation (Smart Loop)
        from core.oracle.automation import oracle_automator
        asyncio.create_task(oracle_automator.start_loop())
        
        # Start Scheduler Loop (The Missing Engine)
        from core.scheduler import scheduler_service
        asyncio.create_task(scheduler_service.start_loop())
        
        print("SYSTEM: Background workers (Factory + Queue + Oracle + Scheduler) started.")
    except Exception as e:
        print(f"ERROR starting workers: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 SHUTDOWN SEQUENCE INITIATED...")
    
    if hasattr(app.state, "watcher_observer") and app.state.watcher_observer:
        print("Stopping Factory Watcher...")
        app.state.watcher_observer.stop()
        # observer.join() might block async loop, usually safe to just stop in async context or run in executor
        # app.state.watcher_observer.join() 
    
    if hasattr(app.state, "queue_worker_task") and app.state.queue_worker_task:
        print("Stopping Queue Worker...")
        app.state.queue_worker_task.cancel()
        try:
            await app.state.queue_worker_task
        except asyncio.CancelledError:
            print("✅ Queue Worker stopped gracefully.")
            
    from core.oracle.automation import oracle_automator
    if oracle_automator.is_running:
        print("Stopping Oracle Automation...")
        oracle_automator.stop()
        
    print("👋 System Shutdown Complete.") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://[::1]:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        # "*",  <-- REMOVED: Cannot use wildcard with allow_credentials=True
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os
from .api.endpoints import content, ingestion, profiles, logs, queue, videos, status, scheduler, oracle, analytics, viral_sounds, audio, logic, batch, templates
from .api import debug_router
from .api import websocket as ws_router

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
app.include_router(status.router, prefix="/api/v1/status", tags=["status"])
app.include_router(scheduler.router, prefix="/api/v1/scheduler", tags=["scheduler"])
app.include_router(oracle.router, prefix="/api/v1/oracle", tags=["oracle"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(viral_sounds.router, prefix="/api/v1/viral-sounds", tags=["viral-sounds"])
app.include_router(audio.router, prefix="/api/v1/audio", tags=["audio"])
app.include_router(logic.router, prefix="/api/v1/logic", tags=["smart-logic"])
app.include_router(batch.router, prefix="/api/v1/batch", tags=["batch-manager"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(debug_router.router, prefix="/api/v1", tags=["debug"])
app.include_router(ws_router.router, tags=["websocket"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Synapse Factory"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
