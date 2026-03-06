import asyncio
import httpx
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
os.environ["POSTGRES_SERVER"] = "localhost"

from core.clipper.monitor import _get_twitch_token, _resolve_broadcaster_info
from core.clipper.models import TwitchTarget

engine = create_engine("postgresql://synapse:synapse_password@localhost/synapse_db")
Session = sessionmaker(bind=engine)
db = Session()

async def sync():
    async with httpx.AsyncClient(timeout=15) as c:
        token = await _get_twitch_token(c)
        targets = db.query(TwitchTarget).all()
        for t in targets:
            info = await _resolve_broadcaster_info(c, token, t.channel_name)
            if info and info.get("profile_image_url"):
                t.profile_image_url = info["profile_image_url"]
                print(f"Updated {t.channel_name} with image: {info['profile_image_url']}")
        db.commit()

if __name__ == "__main__":
    asyncio.run(sync())
