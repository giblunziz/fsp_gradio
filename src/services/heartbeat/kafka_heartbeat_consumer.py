import logging
import os
from datetime import datetime

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from services.heartbeat.kafka_heartbeat_response_producer import KafkaHeartbeatResponseProducer
from src.services import BackgroundConsumer


class KafkaHeartbeatConsumer(BackgroundConsumer):
    __response_producer = KafkaHeartbeatResponseProducer()

    def __init__(self, topic, group_suffix, name):
        super(KafkaHeartbeatConsumer, self).__init__(consumer_name=name, group_suffix=group_suffix, topic=topic)

        log_path = os.getenv('LOG_PATH')
        self.__log_file_name_ = log_path + 'output.log'

        with open(self.__log_file_name_, mode='w') as log_file:
            log_file.truncate()

        handler = logging.FileHandler(self.__log_file_name_)
        self.__logger = logging.getLogger('KAFKA_EVENT_LOGGER')
        self.__logger.setLevel(logging.INFO)
        self.__logger.addHandler(handler)
        logging.info(f"{self._consumer_name} initialized")

    def get_log_filename(self):
        return self.__log_file_name_

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
                            f"{msg.partition()}:{msg.topic()} - {msg.offset()} reached end of partition {{msg.offset()}}")
                    elif msg.error():
                        raise KafkaException(msg.error())
                # decoding avro message
                else:
                    value = self._avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
                    self.__logger.info(f"{msg.partition()}:{msg.topic()} - {value}")
                    # TODO: Create response
                    self._send_response(payload=value)
            self.__logger.info(f"Consumer {self._consumer_name} stopped")
        except KeyboardInterrupt as ex:
            self.__logger.info(f"Consumer {self._consumer_name} stop caused by keyboard interrupt {ex}")
            pass

    def _send_response(self, payload):
        response = payload
        response['response'] = {
            "tsConsumer": datetime.now(),
            "version": "beta-0.0.1"
        }
        self.__response_producer.send_data(response)

