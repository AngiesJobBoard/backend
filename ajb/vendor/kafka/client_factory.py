from kafka import KafkaProducer, KafkaConsumer
from ajb.config.settings import SETTINGS

from .mock import MockKafkaProducer, MockKafkaConsumer
from ..vendor_client_factory import VendorClientFactory


class KafkaProducerFactory(VendorClientFactory):
    @staticmethod
    def _return_mock():
        return MockKafkaProducer()

    @staticmethod
    def _return_client():
        return KafkaProducer(
            bootstrap_servers=[SETTINGS.KAFKA_BOOTSTRAP_SERVER],
            sasl_mechanism="SCRAM-SHA-256",
            security_protocol="SASL_SSL",
            sasl_plain_username=SETTINGS.KAFKA_USERNAME,
            sasl_plain_password=SETTINGS.KAFKA_PASSWORD,
        )


class KafkaConsumerFactory(VendorClientFactory):
    def __init__(self, group_id: str):
        self.group_id = group_id

    @staticmethod
    def _return_mock():
        return MockKafkaConsumer()

    # pylint: disable=arguments-differ
    @staticmethod
    def _return_client(group_id: str):  # type: ignore
        consumer = KafkaConsumer(
            bootstrap_servers=[SETTINGS.KAFKA_BOOTSTRAP_SERVER],
            sasl_mechanism="SCRAM-SHA-256",
            security_protocol="SASL_SSL",
            sasl_plain_username=SETTINGS.KAFKA_USERNAME,
            sasl_plain_password=SETTINGS.KAFKA_PASSWORD,
            auto_offset_reset="earliest",
            group_id=group_id,
        )
        return consumer

    def get_client(self):
        if SETTINGS.LOCAL_TESTING:
            return self._return_mock()
        return self._return_client(self.group_id)
