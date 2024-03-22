import os


def get_bool_from_string(string: str):
    return string.lower() in ("true", "1")


class AppSettings:
    # General
    APP_VERSION: str = os.getenv("APP_VERSION", "0.0.0")
    SYSTEM_USER_EMAIL: str = "sysadmin@angiesjobboard.com"
    APP_DOMAIN: str = os.getenv("APP_DOMAIN", "angiesjobboard.com")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
    APP_NAME: str = os.getenv("APP_NAME", "Angie's Job Board")
    SUPPORT_EMAIL: str = f"support@{APP_DOMAIN}"
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
    KAFKA_BOOTSTRAP_SERVER: str = os.getenv("KAFKA_BOOTSTRAP_SERVER", "localhost:9092")
    KAFKA_USERNAME: str | None = os.getenv("KAFKA_USERNAME")
    KAFKA_PASSWORD: str | None = os.getenv("KAFKA_PASSWORD")
    KAFKA_SASL_MECHANISM: str | None = os.getenv("KAFKA_SASL_MECHANISM", "SCRAM-SHA-256")
    KAFKA_SECURITY_PROTOCOL: str | None = os.getenv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL")
    KAFKA_JWT_SECRET: str = os.getenv("KAFKA_JWT_SECRET", "")

    # Kafka Topics
    KAFKA_USERS_TOPIC: str = os.getenv("KAFKA_USERS_TOPIC", "users")
    KAFKA_COMPANIES_TOPIC: str = os.getenv("KAFKA_COMPANIES_TOPIC", "companies")
    KAFKA_APPLICATIONS_TOPIC: str = os.getenv(
        "KAFKA_APPLICATIONS_TOPIC", "applications"
    )
    KAFKA_WEBHOOKS_TOPIC: str = os.getenv("KAFKA_WEBHOOKS_TOPIC", "webhooks")

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

    # Minio config
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minio")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minio123")
    MINIO_SECURE: bool = get_bool_from_string(os.getenv("MINIO_SECURE", "false"))
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "ajb")

    # Deeplink secrets
    DEFAULT_EXPIRY_HOURS: int = int(os.getenv("RECRUITER_INVITATION_SECRET", 100))
    RECRUITER_INVITATION_SECRET: str = os.getenv("RECRUITER_INVITATION_SECRET", "test")

    # Mixpanel for product analytics
    MIXPANEL_TOKEN: str = os.getenv("MIXPANEL_TOKEN", "38f552bd01fdd7399ad3a2aac8becdba")

    class Config:
        env_file = ".env"


SETTINGS = AppSettings()  # type: ignore
