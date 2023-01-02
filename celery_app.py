from celery import Celery

from constants import (
    BROKER_URL,
    BACKEND_URL,
    AWS_REGION,
    S3_BUCKET,
    CELERY_QUEUE_URL,
    REALTIME_QUEUE_URL,
    SLOW_QUEUE_URL
)

celery_app = Celery(
    'whisper',
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery_app.conf.task_serializer = 'json'
celery_app.conf.result_serializer = 'json'
celery_app.conf.accept_content = ['json']
celery_app.conf.task_routes = {
    'realtime_tasks.process_audio_stream': {'queue': 'whisper-realtime'},
    'slow_tasks.process_audio_stream': {'queue': 'whisper-slow'},
}

# celery_app.conf.result_backend = 's3'

# celery_app.conf.s3_endpoint_url = 'http://localhost:9000'
# celery_app.conf.s3_access_key_id = 'whisper123'
# celery_app.conf.s3_secret_access_key = 'whisper123'
celery_app.conf.s3_bucket = S3_BUCKET

celery_app.conf.broker_transport_options = {
    'region': AWS_REGION,
    'predefined_queues': {
        'celery': {
            'url': CELERY_QUEUE_URL,
        },
        'whisper-realtime': {
            'url': REALTIME_QUEUE_URL,
        },
        'whisper-slow': {
            'url': SLOW_QUEUE_URL,
            # 'access_key_id': 'xxx',
            # 'secret_access_key': 'xxx',
        },
    },
}
