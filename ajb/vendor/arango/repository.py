import typing as t
from arango.database import StandardDatabase, TransactionDatabase
from arango.exceptions import DocumentInsertError
from arango.cursor import Cursor

from ajb.base.constants import BaseConstants
from ajb.config.settings import SETTINGS
from .client_factory import ArangoClientFactory
from .models import Filter, Sort, Join, Operator


class CreateManyInsertError(Exception):
    pass


class ArangoDBRepository:
    def __init__(
        self,
        db: StandardDatabase | TransactionDatabase,
        collection_view_or_graph: str,
        include_soft_deleted: bool = False,
    ):
        self.db = db
        self.collection_view_or_graph = collection_view_or_graph
        self.include_soft_deleted = include_soft_deleted
        self.query_parts = [f"FOR doc IN {self.collection_view_or_graph}"]
        self.joins: list[Join] = []
        self.filters: list[Filter] = []
        self.search_filters: list[Filter] = []
        self.sorts: list[Sort] = []
        self.limit: int | None = 25
        self.offset: int = 0
        self.return_fields: list[str] = []
        self.bind_vars: dict[str, t.Any] = {}

    def get(self, id: str):
        return self.db[self.collection_view_or_graph][id]

    def get_many(self, ids: list[str]):
        return self.db[self.collection_view_or_graph].get_many(ids)

    def create(self, create_dict: dict):
        return self.db[self.collection_view_or_graph].insert(
            create_dict, return_new=True, overwrite=False
        )

    def create_many(self, create_dicts: list[dict]):
        # Forces the use of a transaction on the DB to make sure all documents are created otherwise none are created
        if not isinstance(self.db, TransactionDatabase):
            transaction_db = self.db.begin_transaction(
                write=[self.collection_view_or_graph]
            )
        else:
            transaction_db = self.db
        results = transaction_db[self.collection_view_or_graph].insert_many(
            create_dicts, overwrite=False
        )
        if any(isinstance(result, DocumentInsertError) for result in results):  # type: ignore
            transaction_db.abort_transaction()
            raise CreateManyInsertError
        transaction_db.commit_transaction()
        return results

    def upsert(self, upsert_dict: dict):
        return self.db[self.collection_view_or_graph].insert(
            upsert_dict, return_new=True, overwrite=True
        )

    def upsert_many(self, upsert_dicts: list[dict]):
        return self.db[self.collection_view_or_graph].insert_many(
            upsert_dicts, overwrite=True
        )

    def update(self, update_dict: dict):
        return self.db[self.collection_view_or_graph].update(
            update_dict, return_new=True, merge=True
        )

    def update_many(self, update_dicts: list[dict]):
        return self.db[self.collection_view_or_graph].update_many(
            update_dicts, merge=True
        )

    def delete(self, id: str):
        return bool(self.db[self.collection_view_or_graph].delete(id))

    def delete_many(self, ids: list[str]):
        return bool(self.db[self.collection_view_or_graph].delete_many(ids))  # type: ignore

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

    def _append_text_search_filter(self, filter_index: int, filter_obj: Filter):
        self.query_parts.append(
            f"""
            {'FILTER' if filter_index == 0 else filter_obj.and_or_operator} 
            LOWER({filter_obj.collection_alias}.{filter_obj.field})
            {filter_obj.operator_value} LOWER(@{self.get_next_bind_var_key()})
            """
        )

    def _append_in_search_filter(self, filter_index: int, filter_obj: Filter):
        LIKE_NOT_LIKE_OPERATOR = (
            "LIKE" if filter_obj.operator == Operator.IN else "NOT LIKE"
        )
        self.filters[filter_index].value = f"%{filter_obj.value}%"
        self.query_parts.append(
            f"""
            {'FILTER' if filter_index == 0 else filter_obj.and_or_operator}
            (
                FOR item IN {filter_obj.collection_alias}.{filter_obj.field}
                FILTER LOWER(item) {LIKE_NOT_LIKE_OPERATOR} LOWER(@{self.get_next_bind_var_key()})
                RETURN true
            ) != []
            """
        )

    def _append_array_in_filter(self, filter_index: int, filter_obj: Filter):
        self.query_parts.append(
            f"""
            {'FILTER' if filter_index == 0 else filter_obj.and_or_operator} 
            {filter_obj.collection_alias}.{filter_obj.field}
            IN @{self.get_next_bind_var_key()}
            """
        )

    def _append_default_filter(self, filter_index: int, filter_obj: Filter):
        self.query_parts.append(
            f"""
            {'FILTER' if filter_index == 0 else filter_obj.and_or_operator} 
            {filter_obj.collection_alias}.{filter_obj.field}
            {filter_obj.operator_value} @{self.get_next_bind_var_key()}
            """
        )

    def _append_search_filter(self, filter_index: int, filter_obj: Filter):
        self.query_parts.append(
            f"""
            LOWER({filter_obj.collection_alias}.{filter_obj.field})
            LIKE LOWER(@{self.get_next_bind_var_key()})
            {'OR' if filter_index < len(self.search_filters) - 1 else ''}
            """
        )

    def _append_all_filters(self):
        for i, filter_obj in enumerate(self.filters):
            # If the filter is a text search, use lower
            if filter_obj.operator.is_text_search():
                self._append_text_search_filter(i, filter_obj)
            elif filter_obj.operator.is_in_search():
                self._append_in_search_filter(i, filter_obj)
            elif filter_obj.operator == Operator.ARRAY_IN:
                self._append_array_in_filter(i, filter_obj)
            else:
                self._append_default_filter(i, filter_obj)
            self.bind_vars[self.get_next_bind_var_key()] = filter_obj.search_value

    def _append_all_search_filters(self):
        if self.search_filters:
            self.query_parts.append("FILTER (")
            for i, filter_obj in enumerate(self.search_filters):
                self._append_search_filter(i, filter_obj)
                self.bind_vars[self.get_next_bind_var_key()] = filter_obj.search_value
            self.query_parts.append(" )")

    def _append_all_sorts(self):
        if not self.sorts:
            # Add default sort of desc created
            self.query_parts.append("SORT doc.created_at DESC")
        else:
            sort_fields = ", ".join(
                [
                    f"{sort.collection_alias}.{sort.field} {sort.direction}"
                    for sort in self.sorts
                ]
            )
            self.query_parts.append(f"SORT {sort_fields}")

    def _append_pagination(self):
        if self.limit:
            self.query_parts.append(f"LIMIT {self.offset}, {self.limit}")

    def _format_query_for_joins_or_not(self):
        if self.joins:
            self.query_parts.append(self.format_return_with_joins())
        else:
            self.query_parts.append(self.format_non_join_return())

    def build_query(self) -> str:
        self._append_all_filters()
        self._append_all_search_filters()
        self._append_all_sorts()
        self._append_pagination()
        self._format_query_for_joins_or_not()
        return "\n".join(self.query_parts)

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

    def execute_custom_statement(self, statement: str, bind_vars: dict):
        cursor = t.cast(
            Cursor,
            self.db.aql.execute(statement, bind_vars=bind_vars),
        )
        return list(cursor)


def get_arango_db() -> StandardDatabase:
    return ArangoClientFactory.get_client().db(
        name=SETTINGS.ARANGO_DB_NAME,
        username=SETTINGS.ARANGO_USERNAME,
        password=SETTINGS.ARANGO_PASSWORD,
    )
