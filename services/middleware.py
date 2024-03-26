from kafka.consumer.fetcher import ConsumerRecord

from ajb.vendor.jwt import decode_jwt
from ajb.exceptions import InvalidTokenException
from ajb.config.settings import SETTINGS


def verify_message_header_token(message: ConsumerRecord) -> None:
    is_verified = False
    for header in message.headers:
        if header[0] == "authorization":
            is_verified = bool(decode_jwt(header[1], SETTINGS.KAFKA_JWT_SECRET))
    if not is_verified:
        raise InvalidTokenException()
