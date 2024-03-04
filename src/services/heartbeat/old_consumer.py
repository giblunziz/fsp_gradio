import asyncio
import logging
import os
import socket
from multiprocessing import Process
from threading import Thread

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from constants import HEARTBEAT_TOPIC, KAF_BOOTSTRAP, KAF_KEY_USER, KAF_KEY_PASS, SA_NAME, SR_URL, SR_USERNAME, \
    SR_PASSWORD
from services import Singleton

from src.constants import GROUP_ID_PREFIX


class KafkaConsumer(metaclass=Singleton):
    __topics = []
    __running = False
    __consumer = None
    __thread = None

    def __init__(self, KT_HEARTBEAT_RESPONSE=None):
        # setup logger
        log_path = os.getenv('LOG_PATH')
        log_file_name_ = log_path + 'output.log'

        with open(log_file_name_, mode='w') as log_file:
            log_file.truncate()

        handler = logging.FileHandler(log_file_name_)
        self.__logger = logging.getLogger('KAFKA_EVENT_LOGGER')
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(handler)

        # logging.basicConfig(filename=log_file_name_, level=logging.INFO)

        self.__topics.append(HEARTBEAT_TOPIC)
        # self.__topics.append(KT_HEARTBEAT_RESPONSE)
        self._group_id = os.getenv("KAF_GROUPID")

        self.__schema_registry_client = SchemaRegistryClient(self.__get_schema_registry_conf())
        self.__avro_deserializer = AvroDeserializer(self.__schema_registry_client)

        logging.info("Consumer initialized")

    def __get_consumer_conf(self):
        return {
            "client.id": "svc-fit-app-" + socket.gethostname(),
            "bootstrap.servers": KAF_BOOTSTRAP,
            "ssl.endpoint.identification.algorithm": "https",
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": KAF_KEY_USER,
            "sasl.password": KAF_KEY_PASS,
            "group.id": GROUP_ID_PREFIX + '-hb-consumer',
        }

    def __get_schema_registry_conf(self):
        return {
            'url': SR_URL,
            'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
        }
    def start(self):
        if not self.__running:
            self.__running = True
            self.__consumer = Consumer(self.__get_consumer_conf())
            self.__consumer.subscribe(self.__topics)
            self.__logger.debug("Consumer starting")
            self.__thread = Thread(target=self.__start_listener, name='Kafka consumer listener')
            self.__thread.start()

    def stop(self):
        if self.__running:
            print(self.__thread)
            self.__running = False
            if self.__thread:
                print("Waiting for thread to stop")
                self.__logger.info("Stopping Consumer")
                self.__thread.join()
            self.__thread = None

    def is_running(self):
        return self.__running



    def __start_listener(self):
        self.__running = True
        logging.info("Consumer started")
        self.__logger.info("Consumer started")
        try:
            while self.is_running():
                msg = self.__consumer.poll(timeout=5.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        self.__logger.error(f"{msg.topic()} {msg.partition()} {msg.offset()} reached end of partition {{msg.offset()}}")
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    value = self.__avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
                    # logging.info(str(msg.topic()) + ' : ' + str(value))
                    self.__logger.info(str(msg.topic()) + ' : ' + str(value))
            logging.info("Kafka consumer stopped")
        except KeyboardInterrupt:
            pass

        finally:
            # Close down consumer to commit final offsets.
            self.__consumer.unsubscribe()
            self.__consumer.close()
            self.__running = False
            logging.info("Consumer stopped")
            self.__logger.info("Consumer stopped")
