from typing import cast
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from ajb.base import (
    RequestScope,
    build_and_execute_query,
    build_and_execute_timeseries_query,
    RepoFilterParams,
    Collection,
    Pagination,
)
from ajb.base.events import UserEvent, CompanyEvent
from ajb.vendor.arango.models import Filter, Operator

from .models import AdminSearch, Aggregation


class AdminSearchRepository:
    """
    This class is only meant to be used by an API.
    Other internal functions should not interact with this class directly
    """

    def __init__(self, request_scope: RequestScope):
        self.db = request_scope.db

    def admin_search(
        self,
        search: AdminSearch,
    ) -> tuple[list[dict], int]:
        response = build_and_execute_query(
            db=self.db,
            collection_name=search.collection.value,
            repo_filters=search,
        )
        return cast(tuple[list[dict], int], response)

    def admin_count(
        self,
        search: AdminSearch,
    ) -> int:
        response = build_and_execute_query(
            db=self.db,
            collection_name=search.collection.value,
            repo_filters=search,
            execute_type="count",
        )
        return cast(int, response)

    def get_timeseries_data(
        self,
        collection: Collection,
        start: datetime | None = None,
        end: datetime | None = None,
        aggregation: Aggregation | None = None,
    ) -> tuple[list[dict], int]:
        response = build_and_execute_timeseries_query(
            db=self.db,
            collection_name=collection.value,
            start=start,
            end=end,
            aggregation_datetime_format=(
                aggregation.get_datetime_format() if aggregation else None
            ),
        )
        return cast(tuple[list[dict], int], response)

    def get_action_timeseries_data(
        self,
        event: UserEvent | CompanyEvent | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        aggregation: Aggregation | None = None,
        additional_groupbys: list[str] | None = None,
    ):
        if event:
            filters = [Filter(field="action", value=event.value)]
        else:
            filters = []
        response = build_and_execute_timeseries_query(
            db=self.db,
            collection_name=Collection.COMPANY_ACTIONS.value,
            filters=filters,
            start=start,
            end=end,
            aggregation_datetime_format=(
                aggregation.get_datetime_format() if aggregation else None
            ),
            additional_groupbys=additional_groupbys,  # type: ignore
        )
        return cast(tuple[list[dict], int], response)

    def admin_global_text_search(self, text: str, page: int = 0, page_size=5):
        """Search multiple collections for a given text search"""
        pagination = Pagination(page=page, page_size=page_size)
        users_filters = RepoFilterParams(
            filters=[
                Filter(
                    field="first_name",
                    operator=Operator.CONTAINS,
                    value=text,
                    and_or_operator="OR",
                ),
                Filter(
                    field="last_name",
                    operator=Operator.CONTAINS,
                    value=text,
                    and_or_operator="OR",
                ),
                Filter(
                    field="email",
                    operator=Operator.CONTAINS,
                    value=text,
                    and_or_operator="OR",
                ),
            ],
            pagination=pagination,
        )
        companies_filters = RepoFilterParams(
            filters=[
                Filter(field="name", operator=Operator.CONTAINS, value=text),
            ],
            pagination=pagination,
        )
        jobs_filters = RepoFilterParams(
            filters=[
                Filter(field="position_title", operator=Operator.CONTAINS, value=text),
            ],
            pagination=pagination,
        )

        results = {}
        with ThreadPoolExecutor() as executor:
            results[Collection.USERS] = executor.submit(
                build_and_execute_query,
                db=self.db,
                collection_name=Collection.USERS.value,
                repo_filters=users_filters,
                execute_type="execute",
                return_fields=["first_name", "last_name", "email", "_key"],
            )
            results[Collection.COMPANIES] = executor.submit(
                build_and_execute_query,
                db=self.db,
                collection_name=Collection.COMPANIES.value,
                repo_filters=companies_filters,
                execute_type="execute",
                return_fields=["name", "_key"],
            )
            results[Collection.JOBS] = executor.submit(
                build_and_execute_query,
                db=self.db,
                collection_name=Collection.JOBS.value,
                repo_filters=jobs_filters,
                execute_type="execute",
                return_fields=["position_title", "_key"],
            )
        return {
            collection: result.result()[0] for collection, result in results.items()
        }

    def get_object(self, collection: Collection, object_id: str):
        return self.db.collection(collection.value).get(object_id)
