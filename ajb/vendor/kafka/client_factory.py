from kafka import KafkaProducer, KafkaConsumer
from ajb.config.settings import SETTINGS

from .mock import MockKafkaProducer, MockKafkaConsumer
from ..vendor_client_factory import VendorClientFactory


class KafkaProducerFactory(VendorClientFactory[KafkaProducer]):
    @staticmethod
    def _return_mock():
        return MockKafkaProducer()

    @staticmethod
    def _return_client():
        config = {
            "bootstrap_servers": [SETTINGS.KAFKA_BOOTSTRAP_SERVER],
            "sasl_mechanism": SETTINGS.KAFKA_SASL_MECHANISM,
            "security_protocol": SETTINGS.KAFKA_SECURITY_PROTOCOL,
            "sasl_plain_username": SETTINGS.KAFKA_USERNAME,
            "sasl_plain_password": SETTINGS.KAFKA_PASSWORD,
        }
        non_null_config = {k: v for k, v in config.items() if v is not None}
        return KafkaProducer(**non_null_config)


class KafkaConsumerFactory(VendorClientFactory[KafkaConsumer]):
    def __init__(self, group_id: str):
        self.group_id = group_id

    @staticmethod
    def _return_mock():
        return MockKafkaConsumer()

    # pylint: disable=arguments-differ
    @staticmethod
    def _return_client(group_id: str):  # type: ignore
        config = {
            "bootstrap_servers": [SETTINGS.KAFKA_BOOTSTRAP_SERVER],
            "sasl_mechanism": SETTINGS.KAFKA_SASL_MECHANISM,
            "security_protocol": SETTINGS.KAFKA_SECURITY_PROTOCOL,
            "sasl_plain_username": SETTINGS.KAFKA_USERNAME,
            "sasl_plain_password": SETTINGS.KAFKA_PASSWORD,
            "auto_offset_reset": "earliest",
            "group_id": group_id,
        }
        non_null_config = {k: v for k, v in config.items() if v is not None}
        consumer = KafkaConsumer(**non_null_config)
        return consumer

    def get_client(self):
        if SETTINGS.LOCAL_TESTING:
            return self._return_mock()
        return self._return_client(self.group_id)
