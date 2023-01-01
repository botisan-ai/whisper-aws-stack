from celery import Celery

from constants import BROKER_URL, BACKEND_URL

celery_app = Celery(
    'whisper',
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery_app.conf.task_serializer = 'pickle'
celery_app.conf.result_serializer = 'pickle'
celery_app.conf.accept_content = ['pickle']
celery_app.conf.task_routes = {
    'realtime_tasks.process_audio_stream': {'queue': 'whisper-realtime'},
    'slow_tasks.process_audio_stream': {'queue': 'whisper-slow'},
}

# celery_app.conf.result_backend = 's3'

# celery_app.conf.s3_endpoint_url = 'http://localhost:9000'
# celery_app.conf.s3_access_key_id = 'whisper123'
# celery_app.conf.s3_secret_access_key = 'whisper123'
# celery_app.conf.s3_bucket = 'task-results'

# celery_app.conf.broker_transport_options = {
#     'region': 'elasticmq',
#     'predefined_queues': {
#         'celery': {
#             'url': 'http://localhost:9324/000000000000/celery',
#             'access_key_id': 'xxx',
#             'secret_access_key': 'xxx',
#         },
#         'whisper-realtime': {
#             'url': 'http://localhost:9324/000000000000/whisper-realtime',
#             'access_key_id': 'xxx',
#             'secret_access_key': 'xxx',
#         },
#         'whisper-slow': {
#             'url': 'http://localhost:9324/000000000000/whisper-slow',
#             'access_key_id': 'xxx',
#             'secret_access_key': 'xxx',
#         },
#     },
# }
