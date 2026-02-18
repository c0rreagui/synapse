import asyncio
import sys
import json
import os
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.uploader_monitored import upload_video_monitored
from core.consts import ScheduleStatus

async def main():
    parser = argparse.ArgumentParser(description="Uploader CLI")
    parser.add_argument("--session", required=True, help="Session Name (e.g. tiktok_profile_01)")
    parser.add_argument("--video", required=True, help="Absolute path to video file")
    parser.add_argument("--caption", required=False, default="", help="Caption with hashtags")
    parser.add_argument("--hashtags", required=False, default="", help="JSON string of hashtgas list")
    parser.add_argument("--schedule_time", required=False, help="ISO format schedule time")
    parser.add_argument("--post", action="store_true", help="Post immediately")
    parser.add_argument("--viral_music", action="store_true", help="Enable viral music")
    parser.add_argument("--sound_title", required=False, help="Sound Title")
    parser.add_argument("--privacy", required=False, default="public_to_everyone", help="Privacy Level")
    parser.add_argument("--checksum", required=False, help="MD5 Checksum for integrity check")
    
    args = parser.parse_args()
    
    # Parse hashtags JSON
    hashtags = []
    if args.hashtags:
        try:
            hashtags = json.loads(args.hashtags)
        except:
            hashtags = []

    # Capture outputs from uploader_monitored (but NOT the final JSON print!)
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    result = None
    
    try:
        with redirect_stdout(f_out), redirect_stderr(f_err):
            result = await upload_video_monitored(
                session_name=args.session,
                video_path=args.video,
                caption=args.caption,
                hashtags=hashtags,
                schedule_time=args.schedule_time,
                post=args.post,
                enable_monitor=True,
                viral_music_enabled=args.viral_music,
                sound_title=args.sound_title,
                privacy_level=args.privacy,
                md5_checksum=args.checksum
            )
    except Exception as e:
        result = {
            "status": "error", 
            "message": f"{str(e)} | Stderr: {f_err.getvalue()}"
        }
    
    # [SYN-CRITICAL-FIX] Print Result as JSON to REAL stdout (OUTSIDE redirect context)
    # This was the root cause of "Executor returned None" - the print was being captured!
    try:
        print(json.dumps(result), flush=True)
    except Exception as e:
        # Fallback if result is not serializable
        print(json.dumps({"status": "error", "message": f"Serialization Error: {e}"}), flush=True)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
