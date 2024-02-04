"""
This module contains the base models that are used throughout the application.
"""

import typing as t
from enum import Enum
from contextlib import contextmanager
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field
from arango.database import StandardDatabase, TransactionDatabase
from kafka import KafkaProducer

from ajb.config.settings import SETTINGS
from ajb.helpers.http import modify_query_parameters_in_url
from ajb.vendor.arango.models import Sort, Filter, Operator
from ajb.vendor.jwt import encode_jwt

from ajb.base.constants import BaseConstants
from ajb.base.schema import Collection


class BaseDataModel(BaseModel):
    id: str
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str

    @classmethod
    def from_arango(cls, data: dict):
        data[BaseConstants.ID] = data.pop(BaseConstants.KEY)
        return cls.model_validate(data)


CreateDataSchema = t.TypeVar("CreateDataSchema", bound=BaseModel)
DataSchema = t.TypeVar("DataSchema", bound=BaseDataModel)


class RequestScope(BaseModel):
    """
    Created during a database request, this model is passed around to all
    repositories and services to ensure that the correct user and database
    are being used for all operations.
    """

    user_id: str
    db: StandardDatabase | TransactionDatabase
    user_is_anonymous: bool = False
    kafka_producer: KafkaProducer | None = None
    company_id: str | None  # The company currently being assumed by the user

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create_anonymous_user_scope(
        cls,
        user_agent: str,
        ip_address: str,
        db: StandardDatabase | TransactionDatabase,
        kafka_producer: KafkaProducer | None = None,
    ):
        anonymous_id = ip_address
        return cls(
            user_id=anonymous_id,
            db=db,
            user_is_anonymous=True,
            kafka_producer=kafka_producer,
            company_id=None,
        )

    @contextmanager
    def start_transaction(
        self,
        read_collections: list[Collection],
        write_collections: list[Collection],
    ):
        """
        Starts a transaction, ensuring that no nested transactions occur.
        Yields a new RequestScope with a transaction database.
        Commits or aborts the transaction based on the execution flow.
        """
        if isinstance(self.db, TransactionDatabase):
            raise ValueError("Cannot start a transaction within a transaction")

        transaction_db = self.db.begin_transaction(
            read=read_collections, write=write_collections
        )
        new_scope = RequestScope(
            user_id=self.user_id, db=transaction_db, company_id=self.company_id
        )

        try:
            yield new_scope
        except Exception as exc:
            if transaction_db.transaction_status() != "aborted":
                transaction_db.abort_transaction()
            raise exc
        finally:
            if transaction_db.transaction_status() != "aborted":
                transaction_db.commit_transaction()


@dataclass
class PaginatedResponse(t.Generic[DataSchema]):
    data: list[DataSchema] | list[dict]
    total: int
    next: str | None = None
    prev: str | None = None

    def build_next_and_prev(
        self, url: str, page: int, page_size: int
    ) -> tuple[str, str]:
        next_url = modify_query_parameters_in_url(
            url, {"page": page + 1, "page_size": page_size}
        )
        prev_url = modify_query_parameters_in_url(
            url,
            {
                "page": page - 1 if page > 0 else 0,
                "page_size": page_size,
            },
        )
        return prev_url, next_url


@dataclass
class Pagination:
    page: int = 0
    page_size: int = SETTINGS.DEFAULT_PAGE_SIZE

    def get_limit_offset(self) -> tuple[int, int]:
        return self.page_size, self.page * self.page_size


def build_pagination_response(
    data_and_count: tuple[list[t.Any], int],
    page: int,
    page_size: int,
    url: str,
    pagination_model=PaginatedResponse,
):
    response = pagination_model(data=data_and_count[0], total=data_and_count[1])
    response.prev, response.next = response.build_next_and_prev(url, page, page_size)
    return response


class RepoFilterParams(BaseModel):
    """
    This is the class that is passed to the query methods
    in the repository classes
    """

    pagination: Pagination | None = Pagination()
    sorts: list[Sort] = Field(default_factory=list)
    filters: list[Filter] = Field(default_factory=list)
    search_filters: list[Filter] = Field(default_factory=list)


class QueryFilterParams(BaseModel):
    """
    This is the class that is used to parse the query string parameters
    """

    page: int = Field(default=0, ge=0)
    page_size: int = Field(default=SETTINGS.DEFAULT_PAGE_SIZE, ge=1)
    sorts: str | None = None
    filters: str | None = None
    search: str | None = None
    search_field_override: str | None = None

    def convert_to_repo_filters(
        self,
        search_fields: tuple[str, ...] = BaseConstants.DEFAULT_SEARCH_FIELDS,
    ) -> RepoFilterParams:
        filters = self._create_filters()
        sorts = self._create_sorts()
        search_filters = self._create_search_filters(
            tuple(self.search_field_override.split(","))
            if self.search_field_override
            else search_fields
        )
        pagination = Pagination(page=self.page, page_size=self.page_size)
        return RepoFilterParams(
            pagination=pagination,
            sorts=sorts,
            filters=filters,
            search_filters=search_filters,
        )

    def _create_filters(self) -> list[Filter]:
        if not self.filters:
            return []
        filters = []
        filters_as_dict: dict[str, str] = {}

        for filter in self.filters.split(","):
            field, value = filter.split("=")
            filters_as_dict[field] = value

        for field_and_operator, value in filters_as_dict.items():
            field_parts = field_and_operator.split("__")
            if len(field_parts) == 1:
                field_parts.append("eq")
            if len(field_parts) > 2:
                collection_alias = field_parts[0]
                field_parts = field_parts[1:]
            else:
                collection_alias = "doc"
            filters.append(
                Filter(
                    field=".".join(field_parts[:-1]),
                    operator=Operator.from_query_string(field_parts[-1]),
                    value=value,
                    collection_alias=collection_alias,
                )
            )
        return filters

    def _create_sorts(self) -> list[Sort]:
        if not self.sorts:
            return []
        sorts = []
        for sort in self.sorts.split(","):
            is_desc = False
            if sort.startswith("-"):
                is_desc = True
                sort = sort[1:]

            sort_parts = sort.split("__")
            if len(sort_parts) > 2:
                collection_alias = sort_parts[0]
                sort_text = ".".join(sort_parts[1:])
            else:
                collection_alias = "doc"
                sort_text = ".".join(sort_parts)

            sorts.append(
                Sort(
                    field=sort_text,
                    direction="DESC" if is_desc else "ASC",
                    collection_alias=collection_alias,
                )
            )
        return sorts

    def _create_search_filters(self, search_fields: tuple[str, ...]) -> list[Filter]:
        if not self.search:
            return []
        search_filters = []
        for field in search_fields:
            search_filters.append(
                Filter(
                    field=field,
                    operator=Operator.CONTAINS,
                    value=self.search,
                    and_or_operator="OR",
                )
            )
        return search_filters


class BaseDeepLinkData(BaseModel):
    def convert_to_deeplink_param(
        self, secret: str, expiry: datetime | None = None
    ) -> str:
        return encode_jwt(self.model_dump(), secret, expiry)


class BaseAction(BaseModel):
    action: Enum
    created_at: datetime = datetime.utcnow()
