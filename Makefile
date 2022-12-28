worker:
	celery -A whisper_tasks worker -l INFO

server:
	uvicorn server:app --host 0.0.0.0 --port 6666
