import datetime
import socket
from uuid import uuid4
from constants import *
import logging

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField


def acked(err, msg):
    if err is not None:
        logging.error("Failed to deliver message: %s: %s" % msg.value().decode('utf-8'), str(err))


def load_schema(subject_name):
    SR_URL = os.environ.get('SR_URL')
    SR_USERNAME = os.getenv('SR_USERNAME')
    SR_PASSWORD = os.getenv('SR_PASSWORD')


    schema_registry_conf = {
        'url': SR_URL,
        'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
    }

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    schema = schema_registry_client.get_latest_version(subject_name + "-value")
    return schema.schema.schema_str


def send_data(count = 1):
    producer_config = {
        "client.id": "svc-fit-app-" + socket.gethostname(),
        "bootstrap.servers": KAF_BOOTSTRAP,
        "ssl.endpoint.identification.algorithm": "https",
        "security.protocol": "SASL_SSL",
        "sasl.mechanism": "PLAIN",
        "sasl.username": KAF_KEY_USER,
        "sasl.password": KAF_KEY_PASS,
        # "compression.type": "snappy",
        # "partitioner": "murmur2_random",
        # "acks": "all",
        # "enable.idempotence": True,
    }

    value_schema = load_schema(HEARTBEAT_TOPIC)


    schema_registry_conf = {
        'url': SR_URL,
        'basic.auth.user.info': SR_USERNAME+":"+SR_PASSWORD,
    }


    serializer_conf = {
        # 'auto.register.schemas': True,
        # 'subject.name.strategy': topic_subject_name_strategy

    }

    # Serializers
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    string_serializer = StringSerializer("utf_8")
    avro_serializer = AvroSerializer(
        schema_registry_client=schema_registry_client,
        schema_str=value_schema,
        conf=serializer_conf)

    producer = Producer(producer_config)
    for _ in range(count):
        try:
            key_str = "HEARTBEAT-" + str(uuid4())
            dt = datetime.datetime.now()
            value_str = {
                "reference": str(uuid4()),
                "tsSender": dt,
            }

            logging.info(f"{key_str}: {value_str}")
            producer.produce(topic=HEARTBEAT_TOPIC,
                             key=string_serializer(key_str),
                             value=avro_serializer(value_str, SerializationContext(HEARTBEAT_TOPIC, MessageField.VALUE)),
                             callback=acked)
        except BufferError:
            logging.error("Local producer queue is full ({0} messages awaiting delivery): try again".format(len(producer)))
    producer.flush()

send_data(10)