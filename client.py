import asyncio
import websockets

async def hello():
    async with websockets.connect("ws://localhost:6666/stream/test") as websocket:
        await websocket.send(b"Hello world!")
        await websocket.close()

asyncio.run(hello())
