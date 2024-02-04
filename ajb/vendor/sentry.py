import sentry_sdk

from ajb.config.settings import SETTINGS


def initialize_sentry():
    if SETTINGS.SENTRY_DSN:
        sentry_sdk.init(
            dsn=SETTINGS.SENTRY_DSN,
            traces_sample_rate=SETTINGS.SENTRY_TRACES_RATE,
        )


def capture_exception(exception: Exception):
    sentry_sdk.capture_exception(exception)
