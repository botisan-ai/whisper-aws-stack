from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asyncio import sleep
from pydantic import BaseModel
from celery.result import AsyncResult

# from fastapi import WebSocket
# from starlette.concurrency import run_until_first_complete
# from asyncio import sleep
# from celery.result import AsyncResult

from celery_app import celery_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # TODO: limit the origins when going prod
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranscriptionInput(BaseModel):
    audio: str

class TranscriptionOutput(BaseModel):
    transcription_id: str
    transcription: Optional[str]

@app.post("/transcribe")
async def transcribe_audio(input: TranscriptionInput):
    result = celery_app.send_task(
        'realtime_tasks.process_audio_stream',
        args=[input.audio, ''],
    )
    return TranscriptionOutput(transcription_id=result.id)

@app.get("/transcription/{transcription_id}")
async def get_transcription(transcription_id: str):
    result = AsyncResult(transcription_id, app=celery_app)
    while not result.ready():
        await sleep(0.1)
    response = result.get()
    transcription = response.get('transcription')
    return TranscriptionOutput(transcription_id=transcription_id, transcription=transcription)

# channels: Dict[str, Queue] = {}

# @app.websocket("/stream/{stream_id}")
# async def on_connect(websocket: WebSocket, stream_id: str):
#     await websocket.accept()

#     stream_id = websocket.path_params['stream_id']
#     channels[stream_id] = Queue()

#     await run_until_first_complete(
#         (process_audio_data, {"websocket": websocket, "stream_id": stream_id}),
#         (get_whisper_result, {"websocket": websocket, "stream_id": stream_id}),
#     )

# async def process_audio_data(websocket: WebSocket, stream_id: str):
#     async for audio in websocket.iter_bytes():
#         result = celery_app.send_task(
#             'realtime_tasks.process_audio_stream',
#             args=[audio, stream_id],
#         )
#         await channels[stream_id].put(result)
#     # should be disconnected
#     print('disconnected, cleanup')
#     if stream_id in channels:
#         while not channels[stream_id].empty():
#             await sleep(0.1)
#         print(f'removing channel {stream_id}')
#         del channels[stream_id]

# async def get_whisper_result(websocket: WebSocket, stream_id: str):
#     while True:
#         result: AsyncResult = await channels[stream_id].get()
#         # blocking call might be fine here, since disconnection will terminate this anyway
#         print(f'Got message: {result.get()}')
#         result.forget()
