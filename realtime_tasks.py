from typing import Dict, Any
from base64 import b64decode
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np

from celery_app import celery_app

processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny")
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language='zh', task='transcribe')

@celery_app.task(acks_late=True)
def process_audio_stream(audio: str, stream_id: str) -> Dict[str, Any]:
    audio_bytes = b64decode(audio)
    audio_ndarray = np.frombuffer(audio_bytes, dtype=np.float32)

    inputs = processor(audio_ndarray, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features

    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return {
        'transcription': transcription,
    }
