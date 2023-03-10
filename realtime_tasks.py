from typing import Dict, Any
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np
import boto3
import struct

from celery_app import celery_app

processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny")
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language='zh', task='transcribe')

@celery_app.task(acks_late=True)
def process_audio_stream(
    bucket: str,
    task_id: str,
    timestamp: float,
    stream_id: str,
) -> Dict[str, Any]:
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, f'voice-{task_id}')
    audio_bytes: bytes = obj.get()['Body'].read()

    audio_float_array = struct.unpack(f'>{len(audio_bytes) // 4}f', audio_bytes)
    audio_ndarray = np.array(audio_float_array, dtype=np.float32)
    # audio_ndarray = np.frombuffer(audio_bytes, dtype=np.float32)

    inputs = processor(audio_ndarray, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features

    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    celery_app.send_task(
        'slow_tasks.process_audio_stream',
        args=[bucket, task_id, timestamp, transcription, stream_id],
    )

    return {
        'transcription': transcription,
    }
