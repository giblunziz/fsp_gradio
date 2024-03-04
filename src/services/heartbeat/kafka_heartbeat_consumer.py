import logging
import os

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from src.services import BackgroundConsumer


class KafkaHeartbeatConsumer(BackgroundConsumer):

    def __init__(self, topic, group_suffix, name):
        super(KafkaHeartbeatConsumer,self).__init__(consumer_name=name, group_suffix=group_suffix, topic=topic)

        log_path = os.getenv('LOG_PATH')
        log_file_name_ = log_path + 'output.log'

        with open(log_file_name_, mode='w') as log_file:
            log_file.truncate()

        handler = logging.FileHandler(log_file_name_)
        self.__logger = logging.getLogger('KAFKA_EVENT_LOGGER')
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(handler)
        logging.info(f"{self._consumer_name} initialized")

    def _start_listener(self):

        self.__logger.info(f"Consumer {self._consumer_name} started")
        try:
            while self.is_running():
                # Pooling consumer
                msg = self._bg_consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                # check for message error
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        self.__logger.error(
                            f"{msg.topic()} {msg.partition()} {msg.offset()} reached end of partition {{msg.offset()}}")
                    elif msg.error():
                        raise KafkaException(msg.error())
                # decoding avro message
                else:
                    value = self._avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
                    self.__logger.info(str(msg.topic()) + ' : ' + str(value))
            self.__logger.info(f"Consumer {self._consumer_name} stopped")
        except KeyboardInterrupt as ex:
            self.__logger.info(f"Consumer {self._consumer_name} stop caused by keyboard interrupt {ex}")
            pass


