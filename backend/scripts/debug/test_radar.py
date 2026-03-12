import sys
import asyncio
import httpx
sys.path.append('d:/APPS - ANTIGRAVITY/Synapse/backend')

from core.clipper.radar import scan_category

async def test():
    print("Testing radar on Just Chatting (509658)")
    count = await scan_category('509658')
    print("New streamers found:", count)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('d:/APPS - ANTIGRAVITY/Synapse/backend/.env')
    asyncio.run(test())
