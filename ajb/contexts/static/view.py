from ajb.base import BaseViewRepository, View

from ajb.vendor.arango.repository import AQLQuery
from ajb.vendor.arango.models import Filter, Operator
from .models import StaticDataTypes


class StaticDataViewRepository(BaseViewRepository):
    view = View.STATIC_DATA_VIEW
    search_fields = ("name",)

    def basic_search(
        self, type: StaticDataTypes, search: str | None = None, limit: int | None = None
    ) -> list[str]:
        query = AQLQuery(self.request_scope.db, self.view.value)
        query.add_filter(
            Filter(field="type", operator=Operator.EQUALS, value=type.value)
        )
        if search:
            query.add_search_filter(
                Filter(
                    field="name",
                    operator=Operator.CONTAINS,
                    value=search,
                )
            )
        if limit:
            query.set_pagination(limit=limit)
        query.set_return_fields(["name"])
        results, _ = query.execute()
        return [doc["name"] for doc in results]
