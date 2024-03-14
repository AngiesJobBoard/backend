"""
These are the base repository classes that get extended into the 
parent, single child, and multiple child repositories.

They represent an interaction with a given collection or context.
They are the main connection point between the application and the database.
"""

import typing as t
from warnings import warn
from datetime import datetime
from pydantic import BaseModel
from arango.database import StandardDatabase, TransactionDatabase
from arango.exceptions import DocumentUpdateError, DocumentGetError, DocumentDeleteError
from arango.cursor import Cursor

from ajb.vendor.arango.models import (
    Filter,
    Operator,
    Join,
)
from ajb.vendor.arango.repository import AQLQuery
from ajb.exceptions import EntityNotFound, MultipleEntitiesReturned

from ajb.base.models import (
    DataSchema,
    CreateDataSchema,
    RequestScope,
    RepoFilterParams,
    QueryFilterParams,
    BaseDataModel,
)
from ajb.base.schema import Collection, View
from ajb.base.constants import BaseConstants


def format_to_schema(
    document: t.Any, entity_model: t.Type[BaseDataModel] | None
) -> DataSchema:  # type: ignore
    return entity_model.from_arango(document) if entity_model else document  # type: ignore


def check_if_parent_exists(
    db: StandardDatabase | TransactionDatabase, parent_collection: str, parent_id: str
) -> None:
    try:
        assert db.collection(parent_collection).get(parent_id)
    except AssertionError:
        raise EntityNotFound(collection=parent_collection, entity_id=parent_id)


def format_child_key(parent_collection: str, parent_id: str) -> str:
    return f"{parent_collection}_{parent_id}"


def convert_filter_type_based_on_datamodel(
    model: t.Type[BaseModel], filters: list[Filter]
) -> list[Filter]:
    updated_filters = []
    for filter in filters:
        if filter.field not in model.model_fields:
            updated_filters.append(filter)
            continue
        possible_field_type = t.get_args(model.model_fields[filter.field].annotation)

        if not possible_field_type:
            # Not a tuple type, so just use the annotation
            if not issubclass(model.model_fields[filter.field].annotation, datetime):  # type: ignore
                filter.value = model.model_fields[filter.field].annotation(filter.value)  # type: ignore
        else:
            # It's a tuple type, so use the first type in the tuple
            if not issubclass(possible_field_type[0], datetime):
                filter.value = possible_field_type[0](filter.value)
        updated_filters.append(filter)
    return updated_filters


def build_and_execute_query(
    *,
    db: StandardDatabase | TransactionDatabase,
    collection_name: str,
    joins: list[Join] = [],
    repo_filters: RepoFilterParams | QueryFilterParams | None = None,
    search_fields: tuple[str, ...] = BaseConstants.DEFAULT_SEARCH_FIELDS,
    execute_type: t.Literal["execute", "count"] = "execute",
    data_model: t.Type[BaseModel] | None = None,
    return_fields: list[str] | None = None,
    **kwargs,
) -> tuple[list[dict], int] | int:
    if repo_filters is None:
        repo_filters = RepoFilterParams()
    if isinstance(repo_filters, QueryFilterParams):
        repo_filters = repo_filters.convert_to_repo_filters(search_fields)
    query = AQLQuery(db, collection_name)

    for join in joins:
        query.add_join(join)
    for filter in repo_filters.filters:
        query.add_filter(filter)
    for filter_field, filter_value in kwargs.items():
        query.add_filter(Filter(field=filter_field, value=filter_value))

    # Update the filter types based on the data model
    if data_model:
        query.filters = convert_filter_type_based_on_datamodel(
            data_model, query.filters
        )

    for search_filter in repo_filters.search_filters:
        query.add_search_filter(search_filter)
    for sort in repo_filters.sorts:
        query.add_sort(sort)
    if repo_filters.pagination:
        query.set_pagination(*repo_filters.pagination.get_limit_offset())
    if return_fields:
        query.set_return_fields(return_fields)

    if execute_type == "count":
        return query.execute_count()

    return query.execute()


def build_and_execute_timeseries_query(
    *,
    db: StandardDatabase | TransactionDatabase,
    collection_name: str,
    filters: list[Filter] = [],
    start: datetime | None = None,
    end: datetime | None = None,
    aggregation_datetime_format: str | None = None,
    additional_groupbys: list[str] = [],
) -> tuple[list[dict], int]:
    # Start building the query
    query_text = f"FOR doc IN {collection_name}\n"
    bind_vars = {}

    # Add date filters if provided
    if start:
        query_text += f"FILTER doc.created_at >= '{start.isoformat()}'\n"
    if end:
        query_text += f"FILTER doc.created_at <= '{end.isoformat()}'\n"

    # Apply additional filters
    for filter in filters:
        query_text += (
            f"FILTER doc.{filter.field} {filter.operator.value} {filter.value}\n"
        )

    if aggregation_datetime_format:
        date_string = "DATE_FORMAT(doc.created_at, @date_format)"
        bind_vars["date_format"] = aggregation_datetime_format
    else:
        date_string = "doc.created_at"
    query_text += f"COLLECT date = {date_string}"

    # Add additional groupbys
    for group in additional_groupbys:
        query_text += f", {group} = doc.{group}"
    query_text += " WITH COUNT INTO count\n"

    # Construct the return object
    return_object = "RETURN {"
    all_return_fields = ["date", "count"]
    all_return_fields.extend(additional_groupbys)
    return_object_fields = [f'"{field}": {field}' for field in all_return_fields]
    return_object += ", ".join(return_object_fields) + "}"
    query_text += return_object

    # Execute the query
    cursor = t.cast(Cursor, db.aql.execute(query_text, bind_vars=bind_vars))
    stats = cursor.statistics()
    count = stats["scanned_full"] - stats["filtered"] if stats else 0
    return list(cursor), count


def convert_key_to_id_for_joined_data(
    data: list[dict], joins: list[Join]
) -> list[dict]:
    updated_data = []
    for join in joins:
        if join.is_aggregate:
            continue
        for result in data:
            if join.to_collection_alias in result:
                result[join.to_collection_alias][BaseConstants.ID] = result[
                    join.to_collection_alias
                ][BaseConstants.KEY]
                updated_data.append(result)
    return data


class BaseRepository(t.Generic[CreateDataSchema, DataSchema]):
    collection: Collection
    entity_model: t.Type[BaseDataModel]
    search_fields: tuple[str, ...] = BaseConstants.DEFAULT_SEARCH_FIELDS

    def __init__(
        self,
        request_scope: RequestScope,
    ):
        self.request_scope = request_scope
        self.db = request_scope.db
        self.db_collection = self.db.collection(self.collection.value)

    def get(self, id: str) -> DataSchema:
        try:
            result = self.db_collection.get(id)
        except DocumentGetError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        if result is None:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        return format_to_schema(result, self.entity_model)

    def create(
        self,
        data: CreateDataSchema,
        overridden_id: str | None = None,
    ) -> DataSchema:
        create_dict = {
            **data.model_dump(mode="json"),
            BaseConstants.CREATED_AT: datetime.utcnow().isoformat(),
            BaseConstants.UPDATED_AT: datetime.utcnow().isoformat(),
            BaseConstants.CREATED_BY: self.request_scope.user_id,
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
        }
        if overridden_id is not None:
            create_dict[BaseConstants.KEY] = overridden_id
        results = self.db_collection.insert(
            create_dict, return_new=True, overwrite=True
        )
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def update(self, id: str, data: BaseModel) -> DataSchema:
        update_dict = {
            **data.model_dump(exclude_none=True, mode="json"),
            BaseConstants.UPDATED_AT: datetime.utcnow().isoformat(),
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
            BaseConstants.KEY: id,
        }
        try:
            results = self.db_collection.update(
                update_dict, merge=True, return_new=True
            )
        except DocumentUpdateError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def update_fields(self, id: str, **kwargs) -> DataSchema:
        update_dict = {
            **kwargs,
            BaseConstants.UPDATED_AT: datetime.utcnow().isoformat(),
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
            BaseConstants.KEY: id,
        }
        try:
            results = self.db_collection.update(
                update_dict,
                merge=False,
                return_new=True,
            )
        except DocumentUpdateError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def delete(self, id: str) -> bool:
        try:
            return bool(self.db_collection.delete({BaseConstants.KEY: id}))
        except DocumentDeleteError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)

    def get_one(self, **kwargs) -> DataSchema:
        query = AQLQuery(self.db, self.collection.value)
        for filter_field, filter_value in kwargs.items():
            query.add_filter(
                Filter(field=filter_field, operator=Operator.EQUALS, value=filter_value)
            )
        results, count = query.execute()
        if count > 1:
            raise MultipleEntitiesReturned(entity_name=self.collection.value)
        if count == 0:
            raise EntityNotFound(collection=self.collection.value)
        return format_to_schema(results[0], self.entity_model)

    def query_with_joins(
        self,
        joins: list[Join] = [],
        return_model: t.Type[BaseModel] | None = None,
        repo_filters: RepoFilterParams | QueryFilterParams | None = None,
        **kwargs,
    ):
        response = build_and_execute_query(
            db=self.db,
            collection_name=self.collection.value,
            repo_filters=repo_filters,
            search_fields=self.search_fields,
            data_model=self.entity_model,
            joins=joins,
            **kwargs,
        )
        if isinstance(response, int):
            return [], response
        results, count = response
        results = convert_key_to_id_for_joined_data(results, joins)
        if not return_model:
            return results, count
        return [
            format_to_schema(result, return_model) for result in results  # type: ignore
        ], count

    def get_one_with_joins(
        self,
        joins: list[Join] = [],
        return_model: t.Type[BaseModel] | None = None,
        repo_filters: RepoFilterParams | QueryFilterParams | None = None,
        **kwargs,
    ):
        results, _ = self.query_with_joins(
            joins=joins,
            return_model=return_model,
            repo_filters=repo_filters,
            **kwargs,
        )
        if len(results) > 1:
            raise MultipleEntitiesReturned(entity_name=self.collection.value)
        if len(results) == 0:
            raise EntityNotFound(
                collection=self.collection.value,
                attribute=", ".join(list(kwargs.keys())),
                value=", ".join(list(kwargs.values())),
            )
        return results[0]

    def query(
        self,
        repo_filters: RepoFilterParams | QueryFilterParams | None = None,
        **kwargs,
    ) -> tuple[list[DataSchema], int]:
        response = build_and_execute_query(
            db=self.db,
            collection_name=self.collection.value,
            repo_filters=repo_filters,
            search_fields=self.search_fields,
            data_model=self.entity_model,
            **kwargs,
        )
        if isinstance(response, int):
            return [], response
        results, count = response
        return [
            format_to_schema(result, self.entity_model) for result in results
        ], count

    def get_count(
        self, repo_filters: RepoFilterParams | QueryFilterParams | None = None, **kwargs
    ) -> int:
        response = build_and_execute_query(
            db=self.db,
            collection_name=self.collection.value,
            repo_filters=repo_filters,
            search_fields=self.search_fields,
            data_model=self.entity_model,
            execute_type="count",
            **kwargs,
        )
        if isinstance(response, int):
            return response
        _, count = response
        return count

    def get_with_joins(
        self,
        id: str,
        joins: list[Join],
        return_model: t.Type[BaseDataModel] | None = None,
    ) -> t.Type[BaseDataModel] | dict:
        query = AQLQuery(self.db, self.collection.value)
        for join in joins:
            query.add_join(join)
        query.return_single_document(id)
        results, _ = query.execute()
        if len(results) == 0:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        results = convert_key_to_id_for_joined_data(results, joins)
        if return_model is None:
            return results[0]
        return format_to_schema(results[0], return_model)

    def get_many_by_id(self, document_ids: list[str]) -> list[DataSchema | None]:
        results = self.db_collection.get_many(document_ids)
        return [
            format_to_schema(result, self.entity_model) if result else None
            for result in results  # type: ignore
        ]

    def create_many(
        self, create_list: list[CreateDataSchema], override_ids: list[str] = []
    ) -> list[str]:
        if override_ids and len(create_list) != len(override_ids):
            raise ValueError(
                "Length of override_ids must be equal to length of create_list"
            )
        create_docs = [
            {
                **create_data.model_dump(mode="json"),
                BaseConstants.CREATED_AT: datetime.utcnow().isoformat(),
                BaseConstants.UPDATED_AT: datetime.utcnow().isoformat(),
                BaseConstants.CREATED_BY: self.request_scope.user_id,
                BaseConstants.UPDATED_BY: self.request_scope.user_id,
            }
            for create_data in create_list
        ]
        if override_ids:
            for index, override_id in enumerate(override_ids):
                create_docs[index][BaseConstants.KEY] = override_id
        created_docs = self.db_collection.insert_many(create_docs)
        return [doc[BaseConstants.KEY] for doc in created_docs]  #  type: ignore

    def update_many(
        self, document_updates: dict[str, CreateDataSchema | dict[str, t.Any]]
    ) -> bool:
        updates_as_dict = {
            key: (
                update_data.model_dump(exclude_none=True, mode="json")
                if isinstance(update_data, BaseModel)
                else update_data
            )
            for key, update_data in document_updates.items()
        }
        update_docs = [
            {
                **update_data,
                BaseConstants.UPDATED_AT: datetime.utcnow().isoformat(),
                BaseConstants.UPDATED_BY: self.request_scope.user_id,
                BaseConstants.KEY: key,
            }
            for key, update_data in updates_as_dict.items()
        ]
        self.db_collection.update_many(update_docs, merge=True)
        return True

    def delete_many(self, document_ids: list[str]) -> bool:
        self.db_collection.delete_many(document_ids)  # type: ignore
        return True

    def get_autocomplete(self, field: str, prefix: str) -> list[dict]:
        query = AQLQuery(self.db, self.collection.value)
        query.add_search_filter(
            Filter(field=field, operator=Operator.STARTS_WITH, value=prefix)
        )
        query.set_pagination(limit=5)
        query.set_return_fields([field])
        results, _ = query.execute()
        return results
    
    def increment_field(self, id: str, field: str, amount: int) -> DataSchema:
        statement = f"""
            FOR doc IN {self.collection.value}
            FILTER doc._key == @id
            UPDATE doc WITH {{ {field}: doc.{field} + @amount }} IN {self.collection.value}
            RETURN NEW
        """
        bind_vars = {
            "id": id,
            "amount": amount,
        }
        results = AQLQuery(self.db, self.collection.value).execute_custom_statement(
            statement, bind_vars
        )
        return format_to_schema(results[0], self.entity_model)
    
    def decrement_field(self, id: str, field: str, amount: int) -> DataSchema:
        statement = f"""
            FOR doc IN {self.collection.value}
            FILTER doc._key == @id
            UPDATE doc WITH {{ {field}: doc.{field} - @amount }} IN {self.collection.value}
            RETURN NEW
        """
        bind_vars = {
            "id": id,
            "amount": amount,
        }
        results = AQLQuery(self.db, self.collection.value).execute_custom_statement(
            statement, bind_vars
        )
        return format_to_schema(results[0], self.entity_model)

    def get_sub_entity(self) -> DataSchema:
        raise NotImplementedError("This method is only used by the single child repo")

    def set_sub_entity(self, data: CreateDataSchema) -> DataSchema:
        raise NotImplementedError("This method is only used by the single child repo")


class ParentRepository(BaseRepository[CreateDataSchema, DataSchema]):
    """
    This class extends the base repository and is meant for
    interacting with root level documents.

    An example is a company, this is a root level object
    """


class SingleChildRepository(BaseRepository[CreateDataSchema, DataSchema]):
    """
    This class extends the base repository is meant for interacting with a
    sub-collection of a root level document where there can be only one sub
    collection of the same type.

    An example is a company's details, which there can only be one of
    directly under the company

    This repository includes additional handling for cacheing data. I expect
    that this type of data is better suited for cacheing that the multiple
    child or parent classes above.
    """

    def __init__(
        self,
        request_scope: RequestScope,
        parent_collection: str,
        parent_id: str,
    ):
        super().__init__(request_scope)
        self.parent_collection = parent_collection
        self.parent_id = parent_id
        check_if_parent_exists(self.db, parent_collection, parent_id)

    def get_sub_entity(self) -> DataSchema:
        return self.get(format_child_key(self.parent_collection, self.parent_id))

    def set_sub_entity(self, data: CreateDataSchema) -> DataSchema:
        try:
            return self.update(
                format_child_key(self.parent_collection, self.parent_id), data
            )
        except EntityNotFound:
            return self.create(
                data,
                overridden_id=format_child_key(self.parent_collection, self.parent_id),
            )


class MultipleChildrenRepository(BaseRepository[CreateDataSchema, DataSchema]):
    """
    This class extends the base repository is meant for interacting with a
    sub-collection of a root level document where there can be many
    sub collections of the same type.

    An example is a company's recruiters, which there may be many of directly under the company
    """

    def __init__(
        self,
        request_scope: RequestScope,
        parent_collection: str,
        parent_id: str | None,
    ):
        super().__init__(request_scope)
        self.parent_collection = parent_collection
        self.parent_id = parent_id

        if parent_id is not None:
            check_if_parent_exists(self.db, parent_collection, parent_id)
        else:
            warn("No parent id provided, parent collection may not exist")

    def create(
        self, data: CreateDataSchema, overridden_id: str | None = None
    ) -> DataSchema:
        create_dict = {
            **data.model_dump(mode="json"),
            BaseConstants.CREATED_AT: datetime.utcnow().isoformat(),
            BaseConstants.UPDATED_AT: datetime.utcnow().isoformat(),
            BaseConstants.CREATED_BY: self.request_scope.user_id,
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
            self.parent_collection: self.parent_id,
        }
        if overridden_id is not None:
            create_dict[BaseConstants.KEY] = overridden_id
        results = self.db_collection.insert(create_dict, return_new=True)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )


class BaseViewRepository:
    view: View
    entity_model: t.Type[BaseDataModel] | None = None
    search_fields: tuple[str, ...] = BaseConstants.DEFAULT_SEARCH_FIELDS

    def __init__(
        self,
        request_scope: RequestScope,
    ):
        self.request_scope = request_scope
        self.db = request_scope.db

    def get(self, id: str) -> dict:
        query = AQLQuery(self.db, self.view.value)
        query.add_filter(
            Filter(field=BaseConstants.KEY, operator=Operator.EQUALS, value=id)
        )
        results, _ = query.execute()
        if len(results) == 0:
            raise EntityNotFound(collection=self.view.value, entity_id=id)
        return format_to_schema(results[0], self.entity_model)

    def query(
        self,
        repo_filters: RepoFilterParams | QueryFilterParams | None = None,
        **kwargs,
    ) -> tuple[list[dict], int]:
        response = build_and_execute_query(
            db=self.db,
            collection_name=self.view.value,
            repo_filters=repo_filters,
            search_fields=self.search_fields,
            data_model=self.entity_model,
            **kwargs,
        )
        if isinstance(response, int):
            return [], response
        results, count = response
        return [
            format_to_schema(result, self.entity_model) for result in results
        ], count
