from transformers import WhisperProcessor, WhisperForConditionalGeneration
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from datetime import datetime
import numpy as np
import torch
import boto3
import struct

from constants import AWS_REGION, OPENSEARCH_HOST
from celery_app import celery_app

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, AWS_REGION, service, session_token=credentials.token)

search = OpenSearch(
    hosts = [{'host': OPENSEARCH_HOST, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

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

    audio_float_array = struct.unpack(f'>{len(audio_bytes) // 4}f', audio_bytes)
    audio_ndarray = np.array(audio_float_array, dtype=np.float32)
    # audio_ndarray = np.frombuffer(audio_bytes, dtype=np.float32)

    inputs = processor(audio_ndarray, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.half().to(device)
    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True, normalize=False)[0]

    print(f'from realtime: {transcription_from_realtime}')
    print(f'whisper large: {transcription}')

    document = {
        'timestamp': datetime.utcfromtimestamp(timestamp).isoformat(),
        'bucket': bucket,
        'key': f'voice-{task_id}',
        'transcript_tiny': transcription_from_realtime,
        'transcript_large': transcription,
        # 'stream_id': stream_id,
    }

    search.index(
        index='transcriptions',
        body=document,
        id=task_id,
    )

    return transcription
