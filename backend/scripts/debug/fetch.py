import os
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

async def main():
    client_id = os.getenv("TWITCH_CLIENT_ID")
    client_secret = os.getenv("TWITCH_CLIENT_SECRET")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials")
        r.raise_for_status()
        token = r.json()["access_token"]
        
        e = datetime.now(timezone.utc)
        s = e - timedelta(hours=24)
        print(f"Fetching clips from {s.strftime('%Y-%m-%dT%H:%M:%SZ')} to {e.strftime('%Y-%m-%dT%H:%M:%SZ')}")
        
        r2 = await client.get(
            f"https://api.twitch.tv/helix/clips?first=50&started_at={s.strftime('%Y-%m-%dT%H:%M:%SZ')}&ended_at={e.strftime('%Y-%m-%dT%H:%M:%SZ')}&broadcaster_id=569325723",
            headers={"Client-ID": client_id, "Authorization": f"Bearer {token}"}
        )
        r2.raise_for_status()
        data = r2.json()
        clips = data.get("data", [])
        print(f"Got {len(clips)} clips")
        for c in clips:
            print(f"-> {c['id']}: lang={c.get('language')}, views={c.get('view_count')}, created={c.get('created_at')}")

if __name__ == "__main__":
    asyncio.run(main())
