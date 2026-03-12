import sys
import asyncio
import httpx
import logging
logging.basicConfig(level=logging.INFO)
import httpx
sys.path.append('d:/APPS - ANTIGRAVITY/Synapse/backend')

from core.clipper.monitor import check_target
from core.database import SessionLocal
from core.clipper.models import TwitchTarget

async def test():
    db = SessionLocal()
    target = db.query(TwitchTarget).filter_by(id=4).first()
    print("Testing check_target on target 4 (loud_coringa)")
    print(f"Target settings: lookback={getattr(target, 'lookback_hours', 6)}, min_views={target.min_clip_views}")
    
    # We will manually fetch to see the views
    from core.clipper.monitor import fetch_top_clips
    import httpx
    
    # Need token
    class MockClient:
        pass
    
    # Or just use raw httpx
    async with httpx.AsyncClient() as client:
        # get token first
        import os
        client_id = os.getenv("TWITCH_CLIENT_ID")
        client_secret = os.getenv("TWITCH_CLIENT_SECRET")
        r = await client.post(f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials")
        token = r.json()["access_token"]
        
        # get clips
        from datetime import datetime, timezone, timedelta
        ended_at = datetime.now(timezone.utc)
        started_at = ended_at - timedelta(hours=24)
        
        r2 = await client.get(
            f"https://api.twitch.tv/helix/clips?first=50&started_at={started_at.strftime('%Y-%m-%dT%H:%M:%SZ')}&ended_at={ended_at.strftime('%Y-%m-%dT%H:%M:%SZ')}&broadcaster_id={target.broadcaster_id}",
            headers={"Client-ID": client_id, "Authorization": f"Bearer {token}"}
        )
        clips = r2.json().get("data", [])
        print("SAMPLE CLIPS (up to 10):")
        for c in clips[:10]:
            print(f" -> Clip {c['id']}: lang={c.get('language')}, views={c.get('view_count')}, title={c.get('title')}")

    try:
        idx = await check_target(4)
        print("Job ID returned:", idx)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('d:/APPS - ANTIGRAVITY/Synapse/backend/.env')
    asyncio.run(test())
