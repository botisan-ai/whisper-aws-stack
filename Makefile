-include .env
export

realtime-worker:
	celery -A realtime_tasks worker -l INFO -Q celery,whisper-realtime

slow-worker:
	celery -A slow_tasks worker -l INFO -Q celery,whisper-slow

worker: realtime-worker slow-worker

server:
	uvicorn server:app --host 0.0.0.0 --port 6666
