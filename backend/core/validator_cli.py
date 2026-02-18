import asyncio
import sys
import json
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.profile_validator_worker import validate_profile_worker

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Profile ID required"}))
        return

    profile_id = sys.argv[1]
    headless = True
    if "--headful" in sys.argv:
        headless = False
        # Remove flag so profile_id logic works if mixed (basic implementation)
    
    # Capture/suppress all other output
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    result = None
    try:
        with redirect_stdout(f_out), redirect_stderr(f_err):
            result = await validate_profile_worker(profile_id, headless=headless)
    except Exception as e:
        # If it crashed, we return the error
        # We can optionally log f_err.getvalue() to a file if needed
        result = {"status": "error", "message": f"{str(e)} | Stderr: {f_err.getvalue()}"}
        
    print(json.dumps(result))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
