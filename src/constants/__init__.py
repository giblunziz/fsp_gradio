import os

KAF_BOOTSTRAP = os.environ.get('KAF_BOOTSTRAP')
KAF_KEY_USER = os.getenv('KAF_KEY_USER')
KAF_KEY_PASS = os.getenv('KAF_KEY_PASS')

SR_URL = os.environ.get('SR_URL')
SR_USERNAME = os.getenv('SR_USERNAME')
SR_PASSWORD = os.getenv('SR_PASSWORD')

HEARTBEAT_TOPIC = os.getenv('KT_HEARTBEAT')
HEARTBEAT_RESPONSE_TOPIC = os.getenv('KT_HEARTBEAT_RESPONSE')

SA_NAME = os.getenv('SA_NAME')

USERNAME = os.getenv('USERNAME')

GROUP_ID_PREFIX = SA_NAME + '-' + USERNAME.lower()
