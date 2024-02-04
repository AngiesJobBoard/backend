import json
from kafka import KafkaProducer, KafkaConsumer

from ajb.config.settings import SETTINGS
from ajb.vendor.jwt import generate_jwt
from ajb.vendor.kafka.client_factory import KafkaProducerFactory


class KafkaProducerRepository:
    def __init__(self, producer: KafkaProducer | None = None):
        self.producer = producer or KafkaProducerFactory.get_client()

    def publish(self, topic: str, message: dict) -> None:
        message_token = generate_jwt(SETTINGS.KAFKA_USERNAME, SETTINGS.KAFKA_JWT_SECRET)
        self.producer.send(
            topic,
            json.dumps(message, default=str).encode("utf-8"),
            headers=[("authorization", message_token.encode("utf-8"))],
        )

    def disconnect(self) -> None:
        self.producer.flush()
        self.producer.close()


class KafkaConsumerRepository:
    def __init__(self, consumer: KafkaConsumer):
        self.consumer = consumer

    def poll(
        self, timeout: int = 100, max_records: int = 20, update_offsets: bool = True
    ) -> None:
        self.consumer.poll(timeout, max_records, update_offsets)

    def disconnect(self) -> None:
        self.consumer.close()
