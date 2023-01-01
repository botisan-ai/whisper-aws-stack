import os
from dotenv import dotenv_values

config = {
    **dotenv_values(os.path.join(os.path.dirname(__file__), '.env')),
    **os.environ,
}

BROKER_URL = config.get('BROKER_URL')
BACKEND_URL = config.get('BACKEND_URL')

