from typing import Dict
from fastapi import FastAPI, WebSocket
from starlette.concurrency import run_until_first_complete
from asyncio import Queue, sleep
from celery.result import AsyncResult

from celery_app import celery_app

app = FastAPI()

channels: Dict[str, Queue] = {}

@app.websocket("/stream/{stream_id}")
async def on_connect(websocket: WebSocket, stream_id: str):
    await websocket.accept()

    stream_id = websocket.path_params['stream_id']
    channels[stream_id] = Queue()

    await run_until_first_complete(
        (process_audio_data, {"websocket": websocket, "stream_id": stream_id}),
        (get_whisper_result, {"websocket": websocket, "stream_id": stream_id}),
    )

async def process_audio_data(websocket: WebSocket, stream_id: str):
    async for audio in websocket.iter_bytes():
        result = celery_app.send_task(
            'whisper_tasks.process_audio_stream',
            args=[audio, stream_id],
        )
        await channels[stream_id].put(result)
    # should be disconnected
    print('disconnected, cleanup')
    if stream_id in channels:
        while not channels[stream_id].empty():
            await sleep(0.1)
        print(f'removing channel {stream_id}')
        del channels[stream_id]

async def get_whisper_result(websocket: WebSocket, stream_id: str):
    while True:
        result: AsyncResult = await channels[stream_id].get()
        # blocking call might be fine here, since disconnection will terminate this anyway
        print(f'Got message: {result.get()}')
        result.forget()
