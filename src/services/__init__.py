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
    __running = False
    __thread = None
    __name = 'no_name'

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, name):
        self.__running = False
        self.__name = name
        print(f"BackgroundRunner({self.__name}) initialized")

    def is_running(self):
        return self.__running

    def start(self):
        self.__running = True
        self.__thread = Thread(target=self._start_listener, name=f"Kafka {self.__name} consumer listener")
        self.__thread.start()
        print(f"BackgroundRunner({self.__name}) started")

    def stop(self):
        if self.__running:
            self.__running = False
            if self.__thread:
                print("Waiting for thread to stop")
                self.__thread.join()
            self.__thread = None

    @abc.abstractmethod
    def _start_listener(self):
        raise NotImplementedError


class BackgroundConsumer(BackgroundRunner):
    __topics = []
    __group_suffix = None
    bg_consumer = None
    _consumer_name = None

    def __init__(self, topics: list[str], group_suffix, consumer_name):
        super().__init__(consumer_name)
        self._consumer_name = consumer_name
        self.__topics.append(topics)
        self.__group_suffix = group_suffix
        self.__service_account = os.getenv("SA_NAME")
        self.__group_id = self.__service_account + '-' + self.__group_suffix

        self.__schema_registry_client = SchemaRegistryClient(self.__get_schema_registry_conf())
        self.__avro_deserializer = AvroDeserializer(self.__schema_registry_client)


        logging.info(f"Background Consumer {self._consumer_name} initialized")

    def start(self):
        if not self.is_running():
            print(f"Consumer {self._consumer_name} initializing")
            self.bg_consumer = Consumer(self.__get_consumer_conf())
            self.bg_consumer.subscribe(self.__topics)
            print(f"Consumer {self._consumer_name} starting")
            super().start()
            print(f"Consumer {self._consumer_name} started")

    def stop(self):
        logging.info(f"Consumer {self._consumer_name} stopping")
        super().stop()
        self.bg_consumer.unsubscribe()
        self.bg_consumer.close()
        self.bg_consumer = None
        logging.info(f"Consumer {self._consumer_name} stopped")

    def __get_schema_registry_conf(self):
        return {
            'url': SR_URL,
            'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
        }

    def __get_consumer_conf(self):
        return {
            "client.id": "svc-fit-app-" + socket.gethostname(),
            "bootstrap.servers": KAF_BOOTSTRAP,
            "ssl.endpoint.identification.algorithm": "https",
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": KAF_KEY_USER,
            "sasl.password": KAF_KEY_PASS,
            "group.id": self.__group_id,
        }

    def get_avro_deserializer(self):
        return self.__avro_deserializer
    # @abc.abstractmethod
    # def _start_listener(self):
    #     return

    def _start_listener(self):
        logging.info(f">>> Consumer {self._consumer_name} started")
        deserializer = self.get_avro_deserializer()
        try:
            while self.is_running():
                print(self.bg_consumer)
                msg = self.bg_consumer.poll(timeout=5.0)
                if msg is None:
                    continue
                if msg.error():
                    logging.info(f"Oops: {msg.error()}")
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logging.error(
                            f"{msg.topic()} {msg.partition()} {msg.offset()} reached end of partition {{msg.offset()}}")
                    elif msg.error():
                        logging.error(f">>> Consumer {self._consumer_name} broke: {msg.error()}")
                        raise KafkaException(msg.error())
                else:
                    value = deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
                    # logging.info(str(msg.topic()) + ' : ' + str(value))
                    logging.info(str(msg.topic()) + ' : ' + str(value))
            logging.info(f">>> Consumer {self._consumer_name} stopped")
        except KeyboardInterrupt:
            print("broken !!!")
        finally:
            self.broken()

    def broken(self):
        logging.error(f">>> Consumer {self._consumer_name} broke")
        self.__running = False
        self.bg_consumer.close()

