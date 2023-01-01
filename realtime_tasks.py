from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np

from celery_app import celery_app

processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny")
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language='zh', task='transcribe')

@celery_app.task
def process_audio_stream(audio: bytes, stream_id: str) -> str:
    inputs = processor(np.frombuffer(audio, dtype=np.float32), sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features
    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return transcription
