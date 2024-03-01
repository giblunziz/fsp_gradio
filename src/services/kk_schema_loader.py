import os
from confluent_kafka.schema_registry import SchemaRegistryClient

def load_schema(subject_name):
    SR_URL = os.environ.get('SR_URL')
    SR_USERNAME = os.getenv('SR_USERNAME')
    SR_PASSWORD = os.getenv('SR_PASSWORD')

    # topic = os.getenv('KAF_TOPIC')

    schema_registry_conf = {
        'url': SR_URL,
        'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
    }

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    schema = schema_registry_client.get_latest_version(subject_name+"-value")
    return schema.schema.schema_str


