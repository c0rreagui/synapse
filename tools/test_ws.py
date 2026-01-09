
import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://127.0.0.1:8000/ws/updates"
    print(f"Attempting connection to {uri}")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            msg = await websocket.recv()
            print(f"Received: {msg}")
            
            # Send ping
            await websocket.send("ping")
            pong = await websocket.recv()
            print(f"Received pong: {pong}")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
