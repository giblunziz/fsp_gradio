import abc
import logging
import os
import socket
import time
from pathlib import Path
from threading import Thread

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from constants import SR_URL, SR_USERNAME, SR_PASSWORD, KAF_BOOTSTRAP, KAF_KEY_USER, KAF_KEY_PASS

# Create logs folder
logs_dir = os.getenv('LOG_PATH')
Path(logs_dir).mkdir(parents=True, exist_ok=True)


class Singleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        logging.info(cls.__instances)
        return cls.__instances[cls]


class BackgroundRunner(abc.ABC):
    __instance = None
    _running = False
    _thread = None
    __name = 'no_name'

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, name):
        self._running = False
        self.__name = name
        print(f"BackgroundRunner({self.__name}) initialized")

    def is_running(self):
        return self._running

    def start(self):
        self._running = True
        self._thread = Thread(target=self._start_listener, name=f"Kafka {self.__name} consumer listener")
        self._thread.start()
        print(f"BackgroundRunner({self.__name}) started")

    def stop(self):
        if self._running:
            self._running = False
            if self._thread:
                print("Waiting for thread to stop")
                self._thread.join()
            self._thread = None

    @abc.abstractmethod
    def _start_listener(self):
        raise NotImplementedError


class BackgroundConsumer(BackgroundRunner):
    _topics = []
    _group_suffix = None
    _bg_consumer = None
    _consumer_name = None
    _avro_deserializer = None

    def __init__(self, topic: str, group_suffix, consumer_name):
        super(BackgroundConsumer, self).__init__(consumer_name)
        self._consumer_name = consumer_name
        self._topics.append(topic)
        self._group_suffix = group_suffix
        self._service_account = os.getenv("SA_NAME")
        self._group_id = self._service_account + '-' + self._group_suffix

        self._schema_registry_client = SchemaRegistryClient(self._get_schema_registry_conf())
        self._avro_deserializer = AvroDeserializer(self._schema_registry_client)


        logging.info(f"Background Consumer {self._consumer_name} initialized")

    def start(self):
        if not self.is_running():
            self._running=True
            print(f"Consumer {self._consumer_name} initializing")
            self._bg_consumer = Consumer(self._get_consumer_conf())
            self._bg_consumer.subscribe(self._topics)
            print(f"Consumer {self._consumer_name} starting")
            super().start()
            print(f"Consumer {self._consumer_name} started")

    def stop(self):
        logging.info(f"Consumer {self._consumer_name} stopping")
        super().stop()
        self._bg_consumer.unsubscribe()
        self._bg_consumer.close()
        self._bg_consumer = None
        logging.info(f"Consumer {self._consumer_name} stopped")

    def _get_schema_registry_conf(self):
        return {
            'url': SR_URL,
            'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
        }

    def _get_consumer_conf(self):
        return {
            "client.id": "svc-fit-app-" + socket.gethostname(),
            "bootstrap.servers": KAF_BOOTSTRAP,
            "ssl.endpoint.identification.algorithm": "https",
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": KAF_KEY_USER,
            "sasl.password": KAF_KEY_PASS,
            "group.id": self._group_id,
        }

    def get_avro_deserializer(self):
        return self._avro_deserializer

    @abc.abstractmethod
    def _start_listener(self):
        return

