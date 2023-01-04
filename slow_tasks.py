from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np
import torch
import boto3

from celery_app import celery_app

device = "cuda" if torch.cuda.is_available() else "cpu"

processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2", load_in_8bit=True)
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2", device_map='auto', load_in_8bit=True)
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language='zh', task='transcribe')

@celery_app.task(acks_late=True, ignore_result=True)
def process_audio_stream(
    bucket: str,
    task_id: str,
    timestamp: float,
    transcription_from_realtime: str,
    stream_id: str,
) -> str:
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket, f'voice-{task_id}')
    audio_bytes: bytes = obj.get()['Body'].read()

    audio_ndarray = np.frombuffer(audio_bytes, dtype=np.float32)

    inputs = processor(audio_ndarray, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.half().to(device)
    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True, normalize=False)[0]

    print(f'from realtime: {transcription_from_realtime}')
    print(f'whisper large: {transcription}')

    return transcription
