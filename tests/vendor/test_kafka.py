from datetime import datetime, timedelta, timezone
import pytest

from ajb.vendor.kafka.repository import (
    KafkaConsumerRepository,
    KafkaProducerRepository,
)
from ajb.vendor.kafka.mock import MockKafkaProducer, MockKafkaConsumer
from ajb.vendor.jwt import generate_jwt, decode_jwt
from ajb.exceptions import ExpiredTokenException, InvalidTokenException


def test_generate_jwt():
    token = generate_jwt("test", "test")
    assert isinstance(token, str)


def test_decode_jwt():
    token = generate_jwt(
        "test", "test", expire_datetime=datetime.now() + timedelta(days=1)
    )
    decoded = decode_jwt(token, "test")
    assert isinstance(decoded, dict)
    assert decoded["iss"] == "test"


def test_decode_jwt_expired():
    with pytest.raises(ExpiredTokenException):
        token = generate_jwt(
            "test",
            "test",
            expire_datetime=datetime.now() - timedelta(seconds=60),
        )
        decode_jwt(token, "test")


def test_decode_jwt_invalid():
    with pytest.raises(InvalidTokenException):
        decode_jwt("test", "test")


class TestKafkaProducerRepository:
    client = MockKafkaProducer()
    repository = KafkaProducerRepository(client)

    def test_disconnect(self):
        self.repository.disconnect()


class TestKafkaConsumerRepository:
    client = MockKafkaConsumer()
    repository = KafkaConsumerRepository(client)

    def test_poll(self):
        self.repository.poll()

    def test_disconnect(self):
        self.repository.disconnect()
