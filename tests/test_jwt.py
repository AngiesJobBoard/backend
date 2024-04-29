from datetime import datetime, timedelta, timezone
import pytest

from ajb.vendor.jwt import generate_jwt, encode_jwt, decode_jwt
from ajb.exceptions import ExpiredTokenException, InvalidTokenException


def test_generate_jwt():
    username = "testuser"
    jwt_secret = "testsecret"
    expire_datetime = datetime.now(timezone.utc) + timedelta(seconds=60)
    token = generate_jwt(username, jwt_secret, expire_datetime)
    decoded_token = decode_jwt(token, jwt_secret)
    assert decoded_token["iss"] == username


def test_encode_decode_jwt():
    secret = "testsecret"
    data = {"test": "test"}
    token = encode_jwt(data, secret)
    decoded_token = decode_jwt(token, secret)
    assert decoded_token["test"] == data["test"]


def test_jwt_exceptions():
    expired_jwt = generate_jwt("test", "test", datetime.now() - timedelta(days=1))
    with pytest.raises(ExpiredTokenException):
        decode_jwt(expired_jwt, "test")
    with pytest.raises(InvalidTokenException):
        decode_jwt("test", "test")
