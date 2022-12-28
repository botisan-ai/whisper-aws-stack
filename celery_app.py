from celery import Celery

from constants import REDIS_URL

celery_app = Celery(
    'whisper',
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.task_serializer = 'pickle'
celery_app.conf.result_serializer = 'pickle'
celery_app.conf.accept_content = ['pickle']
