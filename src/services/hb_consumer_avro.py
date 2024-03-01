from confluent_kafka import Consumer, KafkaError, KafkaException
import sys, socket
from constants import *
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
import logging

log_path = os.getenv('LOG_PATH')
_log_file_name_ = log_path + 'output.log'
logging.basicConfig(filename=_log_file_name_, level=logging.INFO)
logging.info("log are redirected to " + _log_file_name_)


# Consumer specific settings prefixed with your namespace
# ex: adeo-dev-europe-west1-APP-PMAGGEN-LM-FR-P1-C2-SALES-BY-LOCATION-V1
topics = []
topics.append(HEARTBEAT_TOPIC)
# topics.append(HEARTBEAT_RESPONSE_TOPIC)
# logging.info(topics)

# kf_log = gr_logger.Logger("kf-events.log")

# A unique string that identifies the consumer group this consumer belongs to.
# This property is required if the consumer uses either the group management functionality by using subscribe(topic) or
# the Kafka-based offset management strategy.
# Must be something like your service account + a free suffix, like "svc-my-account-TEST1"
my_group_id = os.getenv("KAF_GROUPID")

consumer_conf = {
    "client.id": "svc-fit-app-" + socket.gethostname(),
    "bootstrap.servers": KAF_BOOTSTRAP,
    "ssl.endpoint.identification.algorithm": "https",
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "PLAIN",
    "sasl.username": KAF_KEY_USER,
    "sasl.password": KAF_KEY_PASS,
    "group.id": SA_NAME + '-hb-consumer',
}
# Schema Registry client configuration
schema_registry_conf = {
    'url': SR_URL,
    'basic.auth.user.info': SR_USERNAME + ":" + SR_PASSWORD,
}

schema_registry_client = SchemaRegistryClient(schema_registry_conf)
avro_deserializer = AvroDeserializer(schema_registry_client)

consumer = Consumer(consumer_conf)

consumer.subscribe(topics)

try:
    running = True
    while running:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event
                sys.stderr.write(
                    "%% %s [%d] reached end at offset %d\n"
                    % (msg.topic(), msg.partition(), msg.offset())
                )
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            value = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            logging.info(" **** msg **** ")
            logging.info("   Topic     : ", msg.topic())
            logging.info("   Partition : ", msg.partition())
            logging.info("   Offset    : ", msg.offset())
            logging.info("   TimeStamp : ", msg.timestamp())
            logging.info("   Header    : ", msg.headers())
            logging.info("   Key       : ", msg.key())
            logging.info("   Value     : ", value)
            logging.info(str(msg.topic()) + ' : ' + str(value))

except KeyboardInterrupt:
    pass

finally:
    # Close down consumer to commit final offsets.
    consumer.close()
