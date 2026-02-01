import sys
import asyncio
import os
import uvicorn

# FORCE PROACTOR ON WINDOWS (REQUIRED FOR PLAYWRIGHT)
if sys.platform == "win32":
    print("SYSTEM: Forcing WindowsProactorEventLoopPolicy for Playwright compatibility...")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # Ensure we are running from backend dir
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("STARTING SYNAPSE BACKEND (Custom Launcher)")
    
    # Run Uvicorn
    # Note: reload=True might spawn subprocesses. We rely on app.main to enforce policy in children if needed,
    # but this launcher handles the main process.
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=False,
        log_level="info",
        loop="asyncio" 
    )
