from transformers import WhisperProcessor, WhisperForConditionalGeneration
import numpy as np
import torch

from celery_app import celery_app

device = 'cuda' if torch.cuda.is_available() else 'cpu'

processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2", device=device, load_in_8bit=True)
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2", device=device, load_in_8bit=True)
model.config.forced_decoder_ids = processor.get_decoder_prompt_ids(language='zh', task='transcribe')

@celery_app.task
def process_audio_stream(audio: bytes, stream_id: str) -> str:
    inputs = processor(np.frombuffer(audio, dtype=np.float32), sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.half().to(device)
    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True, normalize=False)[0]
    return transcription
