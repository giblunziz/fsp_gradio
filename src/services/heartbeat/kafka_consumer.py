import abc
import logging
import os

from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from services import BackgroundConsumer


class KafkaConsumer(BackgroundConsumer):

    def __init__(self, topics: list[str], group_suffix, consumer_name):
        super().__init__(consumer_name=consumer_name,
                         group_suffix=group_suffix,
                         topics=topics)

        log_path = os.getenv('LOG_PATH')
        log_file_name_ = log_path + 'output.log'

        with open(log_file_name_, mode='w') as log_file:
            log_file.truncate()

        handler = logging.FileHandler(log_file_name_)
        self.__logger = logging.getLogger('KAFKA_EVENT_LOGGER')
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(handler)

    def _start_listener_(self):
        self.__logger.info(f">>> Consumer {self._consumer_name} started")
        deserializer = self.get_avro_deserializer()
        try:
            while self.is_running():
                print(self.bg_consumer)
                msg = self.bg_consumer.poll(timeout=5.0)
                if msg is None:
                    continue
                if msg.error():
                    self.__logger.info(f"Oops: {msg.error()}")
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        self.__logger.error(
                            f"{msg.topic()} {msg.partition()} {msg.offset()} reached end of partition {{msg.offset()}}")
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    value = deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
                    # logging.info(str(msg.topic()) + ' : ' + str(value))
                    self.__logger.info(str(msg.topic()) + ' : ' + str(value))
            self.__logger.info(f">>> Consumer {self._consumer_name} stopped")
        except KeyboardInterrupt:
            print("broken !!!")
