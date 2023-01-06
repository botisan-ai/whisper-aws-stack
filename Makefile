-include .env
export

realtime-worker:
	celery -A realtime_tasks worker -l INFO -Q celery,whisper-realtime

slow-worker:
	celery -A slow_tasks worker -l INFO -Q celery,whisper-slow

worker: realtime-worker slow-worker

server:
	uvicorn server:app --host 0.0.0.0 --port 6666

deploy:
	cdk deploy --outputs-file cdk.out/outputs.json $(args)

destroy:
	cdk destroy $(args)

install-pycurl-mac:
	pip install --no-cache-dir --compile --ignore-installed --install-option="--with-openssl" --install-option="--openssl-dir=/usr/local/opt/openssl@1.1" pycurl
