import typing as t
from copy import deepcopy
from arango.database import StandardDatabase, TransactionDatabase
from arango.cursor import Cursor

from ajb.config.settings import SETTINGS
from .client_factory import ArangoClientFactory
from .models import Filter, Sort, Join, Operator


class AQLQuery:
    def __init__(
        self, db: StandardDatabase | TransactionDatabase, collection_view_or_graph: str
    ):
        self.db = db
        self.collection_view_or_graph = collection_view_or_graph
        self.query_parts = [f"FOR doc IN {self.collection_view_or_graph}"]
        self.joins: list[Join] = []
        self.filters: list[Filter] = []
        self.search_filters: list[Filter] = []
        self.sorts: list[Sort] = []
        self.limit: int | None = 25
        self.offset: int = 0
        self.return_fields: list[str] = []
        self.bind_vars: dict[str, t.Any] = {}

    def _add_non_aggregate_join_parts(self, join: Join):
        self.query_parts.append(
            f"FOR {join.to_collection_alias} IN {join.to_collection}"
        )
        self.query_parts.append(
            f"""FILTER 
            {join.from_collection_alias}.{join.from_collection_join_attr} 
            == 
            {join.to_collection_alias}.{join.to_collection_join_attr}"""
        )

    def _add_aggregate_join_parts(self, join: Join):
        private_join_alias = f"__{join.to_collection_alias}"
        self.query_parts.append(
            f"""LET {join.to_collection_alias} = 
            ( 
                FOR {private_join_alias} IN {join.to_collection}
                FILTER {private_join_alias}.{join.to_collection_join_attr} 
                    == {join.from_collection_alias}.{join.from_collection_join_attr}
                RETURN {private_join_alias}
            )
            """
        )

    def add_join(self, join: Join):
        self.joins.append(join)
        if join.is_aggregate:
            self._add_aggregate_join_parts(join)
        else:
            self._add_non_aggregate_join_parts(join)

    def add_filter(self, filter_obj: Filter):
        self.filters.append(filter_obj)

    def add_search_filter(self, filter_obj: Filter):
        self.search_filters.append(filter_obj)

    def add_sort(self, sort: Sort):
        self.sorts.append(sort)

    def set_pagination(self, limit: int, offset: int = 0):
        self.limit = limit
        self.offset = offset

    def set_return_fields(self, return_fields: list[str]):
        if "_key" not in return_fields:
            return_fields.append("_key")
        self.return_fields = return_fields

    def return_single_document(self, doc_id: str):
        self.filters.append(
            Filter(field="_key", operator=Operator.EQUALS, value=doc_id)
        )

    def format_return_with_joins(self):
        join_return_dict = {}
        for join in self.joins:
            join_return_dict[join.to_collection_alias] = join.to_collection_alias
        return f"RETURN MERGE(doc, {{ {', '.join([f'{alias}: {alias}' for alias in join_return_dict.values()])} }})"

    def format_non_join_return(self):
        if not self.return_fields:
            return "RETURN doc"
        return f"RETURN {{ {', '.join([f'{field}: doc.{field}' for field in self.return_fields])} }}"

    def get_next_bind_var_key(self):
        """Returns a unique key for a bind variable"""
        return f"_BIND_VAR_{len(self.bind_vars)}"

    def build_query(self) -> str:
        # TODO this has grown into spag and meatballs, refactor

        query = deepcopy(self.query_parts)

        # Add filters
        for i, filter_obj in enumerate(self.filters):
            # If the filter is a text search, use lower
            if filter_obj.operator.is_text_search():
                query.append(
                    f"""
                    {'FILTER' if i == 0 else filter_obj.and_or_operator} 
                    LOWER({filter_obj.collection_alias}.{filter_obj.field})
                    {filter_obj.operator_value} LOWER(@{self.get_next_bind_var_key()})
                    """
                )
            elif filter_obj.operator.is_in_search():
                LIKE_NOT_LIKE_OPERATOR = "LIKE" if filter_obj.operator == Operator.IN else "NOT LIKE"
                self.filters[i].value = f"%{filter_obj.value}%"
                query.append(
                    f"""
                    {'FILTER' if i == 0 else filter_obj.and_or_operator}
                    (
                        FOR item IN {filter_obj.collection_alias}.{filter_obj.field}
                        FILTER LOWER(item) {LIKE_NOT_LIKE_OPERATOR} LOWER(@{self.get_next_bind_var_key()})
                        RETURN true
                    ) != []
                    """
                )
            elif filter_obj.operator == Operator.ARRAY_IN:
                query.append(
                    f"""
                    {'FILTER' if i == 0 else filter_obj.and_or_operator} 
                    {filter_obj.collection_alias}.{filter_obj.field}
                    IN @{self.get_next_bind_var_key()}
                    """
                )
            else:
                query.append(
                    f"""
                    {'FILTER' if i == 0 else filter_obj.and_or_operator} 
                    {filter_obj.collection_alias}.{filter_obj.field}
                    {filter_obj.operator_value} @{self.get_next_bind_var_key()}
                    """
                )
            self.bind_vars[self.get_next_bind_var_key()] = filter_obj.search_value

        # Add search filters (AND (grouped ORs))
        if self.search_filters:
            query.append("FILTER (")
            for i, filter_obj in enumerate(self.search_filters):
                query.append(
                    f"""
                    LOWER({filter_obj.collection_alias}.{filter_obj.field})
                    LIKE LOWER(@{self.get_next_bind_var_key()})
                    {'OR' if i < len(self.search_filters) - 1 else ''}
                    """
                )
                self.bind_vars[self.get_next_bind_var_key()] = filter_obj.search_value
            query.append(" )")

        # Add sorts
        if not self.sorts:
            # Add default sort of desc created
            query.append("SORT doc.created_at DESC")
        else:
            sort_fields = ", ".join(
                [
                    f"{sort.collection_alias}.{sort.field} {sort.direction}"
                    for sort in self.sorts
                ]
            )
            query.append(f"SORT {sort_fields}")

        # Add pagination
        if self.limit:
            query.append(f"LIMIT {self.offset}, {self.limit}")

        if self.joins:
            query.append(self.format_return_with_joins())
        else:
            query.append(self.format_non_join_return())

        return "\n".join(query)

    def execute_count(self) -> int:
        self.limit = None
        query = self.build_query()
        cursor = t.cast(
            Cursor,
            self.db.aql.execute(query, bind_vars=self.bind_vars, count=True),
        )
        return cursor.count() or 0

    def execute(self) -> tuple[list[dict[str, t.Any]], int]:
        query = self.build_query()
        cursor = t.cast(
            Cursor,
            self.db.aql.execute(
                query, bind_vars=self.bind_vars, count=bool(self.joins)
            ),
        )
        if self.joins:
            count = cursor.count() or 0
        else:
            stats = cursor.statistics()
            count = stats["scanned_full"] - stats["filtered"] if stats else 0
        return list(cursor), count


def get_arango_db() -> StandardDatabase:
    return ArangoClientFactory.get_client().db(
        name=SETTINGS.ARANGO_DB_NAME,
        username=SETTINGS.ARANGO_USERNAME,
        password=SETTINGS.ARANGO_PASSWORD,
    )
