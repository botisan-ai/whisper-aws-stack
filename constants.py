import os
from dotenv import dotenv_values

config = {
    **dotenv_values(os.path.join(os.path.dirname(__file__), '.env')),
    **os.environ,
}

BROKER_URL = config.get('BROKER_URL')
BACKEND_URL = config.get('BACKEND_URL')

AWS_REGION = config.get('AWS_REGION')
S3_BUCKET = config.get('S3_BUCKET')
CELERY_QUEUE_URL = config.get('CELERY_QUEUE_URL')
REALTIME_QUEUE_URL = config.get('REALTIME_QUEUE_URL')
SLOW_QUEUE_URL = config.get('SLOW_QUEUE_URL')
