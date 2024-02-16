import os


def get_bool_from_string(string: str):
    return string.lower() in ("true", "1")


class AppSettings:
    # General
    APP_VERSION: str = os.getenv("APP_VERSION", "0.0.0")
    SYSTEM_USER_EMAIL: str = "mike@angiesjobboard.com"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
    DEFAULT_PAGE_SIZE: int = 25

    # Firebase config
    FIRESTORE_APP_NAME: str = "ajb"
    FIRESTORE_JSON_CONFIG: str = os.getenv("FIRESTORE_JSON_CONFIG", "")
    FIREBASE_FILE_STORAGE_BUCKET: str = os.getenv("FIREBASE_FILE_STORAGE_BUCKET", "")

    # Openai config
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "")

    # Clerk config
    CLERK_JWT_PEM_KEY: str = os.getenv("CLERK_JWT_PEM_KEY", "").replace(r"\n", "\n")
    CLERK_TOKEN_LEEWAY: int = int(os.getenv("CLERK_TOKEN_LEEWAY", "3600"))
    CLERK_USER_WEBHOOK_SECRET: str = os.getenv("CLERK_USER_WEBHOOK_SECRET", "")
    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")

    LOCAL_TESTING: bool = get_bool_from_string(os.getenv("LOCAL_TESTING", "false"))
    ENABLED_KAFKA_EVENTS: bool = get_bool_from_string(
        os.getenv("ENABLED_KAFKA_EVENTS", "false")
    )

    # Kafka config
    KAFKA_BOOTSTRAP_SERVER: str = os.getenv("KAFKA_BOOTSTRAP_SERVER", "")
    KAFKA_REST_URL: str = os.getenv("KAFKA_REST_URL", "")
    KAFKA_USERNAME: str = os.getenv("KAFKA_USERNAME", "")
    KAFKA_PASSWORD: str = os.getenv("KAFKA_PASSWORD", "")
    KAFKA_JWT_SECRET: str = os.getenv("KAFKA_JWT_SECRET", "")

    # Sendgrid config
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "")

    # Twilio config
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Sentry config
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_TRACES_RATE: float = 1.0

    # Arango config
    ARANGO_URL: str = os.getenv("ARANGO_URL", "http://localhost:8529")
    ARANGO_USERNAME: str = os.getenv("ARANGO_USERNAME", "root")
    ARANGO_PASSWORD: str = os.getenv("ARANGO_PASSWORD", "root")
    ARANGO_DB_NAME: str = os.getenv("ARANGO_DB_NAME", "ajb")

    # Google API
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Deeplink secrets
    DEFAULT_EXPIRY_HOURS: int = int(os.getenv("RECRUITER_INVITATION_SECRET", 100))
    RECRUITER_INVITATION_SECRET: str = os.getenv("RECRUITER_INVITATION_SECRET", "test")

    class Config:
        env_file = ".env"


SETTINGS = AppSettings()  # type: ignore
