from celery_app import celery_app

@celery_app.task
def process_audio_stream(audio: bytes, stream_id: str):
    print(f'Processing audio: {audio} for stream: {stream_id}')
    return audio
