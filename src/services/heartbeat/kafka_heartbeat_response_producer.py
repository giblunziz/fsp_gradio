import datetime
import logging
import os
import socket
import time
from threading import Thread
from uuid import uuid4

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient, topic_subject_name_strategy
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField

from constants import KAF_BOOTSTRAP, KAF_KEY_USER, KAF_KEY_PASS, SR_URL, SR_USERNAME, SR_PASSWORD, \
    HEARTBEAT_RESPONSE_TOPIC
from services import Singleton


class KafkaHeartbeatResponseProducer(metaclass=Singleton):
    __auto_mode = False
    __thread = None
    __topic = None

    def __init__(self):
        self.__topic = HEARTBEAT_RESPONSE_TOPIC
        value_schema = self.__load_schema(self.__topic)

        # Serializers
        schema_registry_client = SchemaRegistryClient(self.__get_schema_registry_config())
        self.__string_serializer = StringSerializer("utf_8")
        self.__avro_serializer = AvroSerializer(
            schema_registry_client=schema_registry_client,
            schema_str=value_schema,
            conf=self.__get_serializer_config())

        self.__producer = Producer(self.__get_producer_config())

    def __acked(self, err, msg):
        if err is not None:
            logging.error("Failed to deliver message: %s: %s" % msg.value().decode('utf-8'), str(err))

    def __load_schema(self, subject_name):
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

    def __get_producer_config(self):
        return {
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

    def __get_serializer_config(self):
        return {
            'auto.register.schemas': True,
            'subject.name.strategy': topic_subject_name_strategy
        }

    def __get_schema_registry_config(self):
        return {
            'url': SR_URL,
            'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
        }

    def start_auto_mode(self, delay = 1):
        if not self.__thread:
            self.__auto_mode = True
            self.__thread = Thread(target=self.__auto_launch, args=(delay*60,))
            self.__thread.start()

    def stop_auto_mode(self, delay):
        if self.__thread:
            self.__auto_mode = False
            self.__thread.join()
            self.__thread = None

    def __auto_launch(self, delay):
        self.__auto_mode = True
        while self.__auto_mode:
            time.sleep(delay)
            self.send_data(1)


    def send_data(self, payload):

        try:
            key_str = "HEARTBEAT-R-" + str(uuid4())
            print(f"{key_str}: {payload}")

            self.__producer.produce(topic=self.__topic,
                                    key=self.__string_serializer(key_str),
                                    value=self.__avro_serializer(payload,
                                                                 SerializationContext(self.__topic,
                                                                                      MessageField.VALUE)),
                                    callback=self.__acked)
        except BufferError:
            logging.error(
                "Local producer queue is full ({0} messages awaiting delivery): try again".format(
                    len(self.__producer)))
        self.__producer.flush()
