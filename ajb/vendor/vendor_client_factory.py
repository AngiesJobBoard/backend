"""
The base class for all vendor client factories
"""

import typing as t
from ajb.config.settings import SETTINGS


T = t.TypeVar("T")  # This represents the type of the client (the client class object)


class VendorClientFactory(t.Generic[T]):
    @staticmethod
    def _return_client():
        raise NotImplementedError

    @staticmethod
    def _return_mock():
        raise NotImplementedError

    @classmethod
    def get_client(cls) -> T:
        if SETTINGS.LOCAL_TESTING:
            return cls._return_mock()
        return cls._return_client()
