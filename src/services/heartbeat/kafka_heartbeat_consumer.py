import logging

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from services import BackgroundConsumer


class KafkaHeartbeatConsumer(BackgroundConsumer):

    def __init__(self, topic: list[str], group_suffix, name=None):
        super().__init__(name=name, group_suffix=group_suffix, topic=topic)

        logging.info(f"{self.__name} initialized")

    def __start_listener(self):
        self.__running = True
        logging.info(f"Consumer {self.__name} started")
        try:
            while self.is_running():
                msg = self.__consumer.poll(timeout=5.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logging.error(
                            f"{msg.topic()} {msg.partition()} {msg.offset()} reached end of partition {{msg.offset()}}")
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    value = self.__avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
                    # logging.info(str(msg.topic()) + ' : ' + str(value))
            logging.info(f"Consumer {self.__name} stopped")
        except KeyboardInterrupt:
            pass


