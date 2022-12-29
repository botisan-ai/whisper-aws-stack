import asyncio
import websockets
import sounddevice as sd
import numpy as np
import torch

sd.default.samplerate = 16000
sd.default.device = 'MacBook Pro Microphone'
sd.default.channels = 1
sd.default.dtype = 'float32'
sd.default.blocksize = int(16000 / 1000 * 50)

# async def hello():
#     async with websockets.connect("ws://localhost:6666/stream/test") as websocket:
#         await websocket.send(b"Hello world!")
#         await websocket.close()

# asyncio.run(hello())

model, silero_utils = torch.hub.load('snakers4/silero-vad', 'silero_vad', force_reload=False)

async def get_voice_buffer_from_microphone():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    def callback(data: np.ndarray, frame_count: int, time_info, status):
        loop.call_soon_threadsafe(queue.put_nowait, data.copy().squeeze())

    stream = sd.InputStream(callback=callback)

    with stream:
        consecutive_silence = 0
        buffer = b''
        while True:
            data: np.ndarray = await queue.get()
            confidence = model(torch.from_numpy(data), sd.default.samplerate).item()
            if confidence > 0.5:
                consecutive_silence = 0
                buffer += data.tobytes()
            else:
                consecutive_silence += 1
                if consecutive_silence > 5 and len(buffer) > 0:
                    yield buffer
                    consecutive_silence = 0
                    buffer = b''

async def main():
    print('Main app ready')
    async with websockets.connect("ws://localhost:6666/stream/test") as websocket:
        print('Connected to websocket server')
        async for data in get_voice_buffer_from_microphone():
            await websocket.send(data)
        # await websocket.close()

if __name__ == '__main__':
    asyncio.run(main())
