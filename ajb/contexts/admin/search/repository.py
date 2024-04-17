from typing import cast, Literal
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
from ajb.vendor.arango.models import Filter, Operator

from .models import AdminSearch, Aggregation


class AdminSearchRepository:
    """
    This class is only meant to be used by an API.
    Other internal functions should not interact with this class directly
    """

    def __init__(self, request_scope: RequestScope):
        self.db = request_scope.db

    def _get_repo_params(self, search: AdminSearch):
        repo_params = search.convert_to_repo_filters()

        if search.start:
            repo_params.filters.append(
                Filter(
                    field="created_at",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=search.start.isoformat(),
                )
            )
        if search.end:
            repo_params.filters.append(
                Filter(
                    field="created_at",
                    operator=Operator.LESS_THAN_EQUAL,
                    value=search.end.isoformat(),
                )
            )
        return repo_params

    def admin_search(
        self,
        search: AdminSearch,
    ) -> tuple[list[dict], int]:
        response = build_and_execute_query(
            db=self.db,
            collection_name=search.collection.value,
            repo_filters=self._get_repo_params(search),
        )
        return cast(tuple[list[dict], int], response)

    def admin_count(
        self,
        search: AdminSearch,
    ) -> int:
        response = build_and_execute_query(
            db=self.db,
            collection_name=search.collection.value,
            repo_filters=self._get_repo_params(search),
            execute_type="count",
        )
        return cast(int, response)

    def _convert_timeseries_data(
        self, data: tuple[list[dict], int]
    ) -> dict[Literal["data"], dict[datetime, int]]:
        return {"data": {
            row["date"]: row["count"]
            for row in data[0]
        }}

    def get_timeseries_data(
        self,
        collection: Collection,
        start: datetime | None = None,
        end: datetime | None = None,
        aggregation: Aggregation | None = None,
    ) -> dict[Literal["data"], dict[datetime, int]]:
        response = build_and_execute_timeseries_query(
            db=self.db,
            collection_name=collection.value,
            start=start,
            end=end,
            aggregation_datetime_format=(
                aggregation.get_datetime_format() if aggregation else None
            ),
        )
        return self._convert_timeseries_data(response)

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
