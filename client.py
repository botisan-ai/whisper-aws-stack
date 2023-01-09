import asyncio
# import websockets
import sounddevice as sd
import numpy as np
import torch
import aiohttp
from base64 import b64encode

sd.default.samplerate = 16000
sd.default.device = 'MacBook Pro Microphone'
sd.default.channels = 1
sd.default.dtype = 'float32'
sd.default.blocksize = int(16000 / 1000 * 50)

model, silero_utils = torch.hub.load('snakers4/silero-vad', 'silero_vad', force_reload=False)

async def get_voice_buffer_from_microphone():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    def callback(data: np.ndarray, frame_count: int, time_info, status):
        loop.call_soon_threadsafe(queue.put_nowait, data.copy().squeeze())

    stream = sd.InputStream(callback=callback)

    with stream:
        consecutive_silence = 0
        has_voice = False
        buffers = []
        while True:
            data: np.ndarray = await queue.get()
            confidence = model(torch.from_numpy(data), sd.default.samplerate).item()
            if confidence > 0.5:
                has_voice = True
                consecutive_silence = 0
                buffers.append(data)
            else:
                if has_voice:
                    consecutive_silence += 1
                    buffers.append(data)
                else:
                    buffers.append(data)
                    # always keep the last 5 buffered items
                    buffers = buffers[-5:]
                if consecutive_silence > 5 and len(buffers) > 10:
                    yield b''.join([d.tobytes() for d in buffers])
                    consecutive_silence = 0
                    has_voice = False
                    buffers = []

async def main():
    print('Main app ready')
    # async with websockets.connect("ws://localhost:6666/stream/test") as websocket:
    #     print('Connected to websocket server')
        # async for data in get_voice_buffer_from_microphone():
        # await websocket.send(data)
        # await websocket.close()

    async with aiohttp.ClientSession() as session:
        async for data in get_voice_buffer_from_microphone():
            async with session.post('http://localhost:6666/transcribe', json={ 'audio': b64encode(data).decode() }) as transcribe_response:
                transcribe_response_json = await transcribe_response.json()
                transcription_id = transcribe_response_json.get('transcription_id')
                async with session.get(f'http://localhost:6666/transcription/{transcription_id}') as transcription_response:
                    transcription_response_json = await transcription_response.json()
                    print(transcription_response_json.get('transcription'))

if __name__ == '__main__':
    asyncio.run(main())
