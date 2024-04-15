from datetime import datetime, timedelta, timezone
import jwt

from ajb.config.settings import SETTINGS
from ajb.exceptions import ExpiredTokenException, InvalidTokenException


def generate_jwt(
    username: str | None,
    jwt_secret: str,
    expire_datetime: datetime = (datetime.now(timezone.utc) + timedelta(seconds=60)),
) -> str:
    payload = {
        "iss": username or "ajb",
        "iat": datetime.now(timezone.utc),
        "exp": expire_datetime,
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def encode_jwt(data: dict, secret: str, expiry: datetime | None = None) -> str:
    data["exp"] = expiry or (
        datetime.now(timezone.utc) + timedelta(hours=SETTINGS.DEFAULT_EXPIRY_HOURS)
    )
    return jwt.encode(
        data, secret, algorithm="HS256", headers={"typ": "JWT", "alg": "HS256"}
    )


def decode_jwt(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenException()
    except jwt.InvalidTokenError:
        raise InvalidTokenException()
