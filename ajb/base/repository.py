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
from arango.exceptions import (
    DocumentUpdateError,
    DocumentGetError,
    DocumentDeleteError,
    DocumentInsertError,
)
from arango.cursor import Cursor

from ajb.vendor.arango.models import Filter, Operator, Join, Sort
from ajb.vendor.arango.repository import ArangoDBRepository, CreateManyInsertError
from ajb.exceptions import EntityNotFound, MultipleEntitiesReturned, FailedToCreate

from ajb.base.models import (
    DataSchema,
    CreateDataSchema,
    RequestScope,
    RepoFilterParams,
    QueryFilterParams,
    BaseDataModel,
    Pagination,
)
from ajb.base.schema import Collection, View
from ajb.base.constants import BaseConstants


def format_to_schema(
    document: t.Any, entity_model: t.Type[BaseDataModel] | None
) -> DataSchema:  # type: ignore
    return entity_model.from_arango(document) if entity_model else document  # type: ignore


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
                try:
                    filter.value = possible_field_type[0](filter.value)
                except ValueError:
                    # If the value can't be converted to the type, just pass it through
                    pass
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
    query = ArangoDBRepository(db, collection_name)

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
    aggregation_datetime_format: str | None = None,
    additional_groupbys: list[str] = [],
) -> tuple[list[dict], int]:
    query_text = f"FOR doc IN {collection_name}\n"
    bind_vars: t.MutableMapping[str, str] = {}

    for idx, filter in enumerate(filters):
        if idx == 0:
            query_text += (
                f"FILTER doc.{filter.field} {filter.operator.value} '{filter.value}'\n"
            )
        else:
            query_text += (
                f"AND doc.{filter.field} {filter.operator.value} '{filter.value}'\n"
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
    cursor = t.cast(Cursor, db.aql.execute(query_text, bind_vars=bind_vars))  # type: ignore
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
        self.db = ArangoDBRepository(request_scope.db, self.collection.value)

    def get(self, id: str) -> DataSchema:
        try:
            result = self.db.get(id)
        except DocumentGetError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        if result is None:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        return format_to_schema(result, self.entity_model)

    def create(
        self,
        data: CreateDataSchema,
        overridden_id: str | None = None,
        parent_collection: str | None = None,
        parent_id: str | None = None,
    ) -> DataSchema:
        create_dict = {
            **data.model_dump(mode="json"),
            BaseConstants.CREATED_AT: datetime.now().isoformat(),
            BaseConstants.UPDATED_AT: datetime.now().isoformat(),
            BaseConstants.CREATED_BY: self.request_scope.user_id,
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
        }
        if overridden_id is not None:
            create_dict[BaseConstants.KEY] = overridden_id
        if parent_collection and parent_id:
            create_dict[parent_collection] = parent_id
        try:
            results = self.db.create(create_dict)
        except DocumentInsertError:
            raise FailedToCreate(self.collection.value, overridden_id)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def update(self, id: str, data: BaseModel, merge: bool = True) -> DataSchema:
        update_dict = {
            **data.model_dump(exclude_none=True, mode="json"),
            BaseConstants.UPDATED_AT: datetime.now().isoformat(),
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
            BaseConstants.KEY: id,
        }
        try:
            results = self.db.update(update_dict, merge)
        except DocumentUpdateError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def update_fields(self, id: str, **kwargs) -> DataSchema:
        update_dict = {
            **kwargs,
            BaseConstants.UPDATED_AT: datetime.now().isoformat(),
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
            BaseConstants.KEY: id,
        }
        try:
            results = self.db.update(update_dict)
        except DocumentUpdateError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def upsert(
        self,
        data: CreateDataSchema,
        overridden_id: str | None = None,
        parent_collection: str | None = None,
        parent_id: str | None = None,
    ) -> DataSchema:
        create_dict = {
            **data.model_dump(mode="json"),
            BaseConstants.CREATED_AT: datetime.now().isoformat(),
            BaseConstants.UPDATED_AT: datetime.now().isoformat(),
            BaseConstants.CREATED_BY: self.request_scope.user_id,
            BaseConstants.UPDATED_BY: self.request_scope.user_id,
        }
        if overridden_id is not None:
            create_dict[BaseConstants.KEY] = overridden_id
        if parent_collection and parent_id:
            create_dict[parent_collection] = parent_id
        results = self.db.upsert(create_dict)
        return format_to_schema(
            t.cast(dict, results)[BaseConstants.NEW], self.entity_model
        )

    def upsert_many(
        self, create_list: list[CreateDataSchema], override_ids: list[str] = []
    ) -> list[str]:
        if override_ids and len(create_list) != len(override_ids):
            raise ValueError(
                "Length of override_ids must be equal to length of create_list"
            )
        create_docs = [
            {
                **create_data.model_dump(mode="json"),
                BaseConstants.CREATED_AT: datetime.now().isoformat(),
                BaseConstants.UPDATED_AT: datetime.now().isoformat(),
                BaseConstants.CREATED_BY: self.request_scope.user_id,
                BaseConstants.UPDATED_BY: self.request_scope.user_id,
            }
            for create_data in create_list
        ]
        if override_ids:
            for index, override_id in enumerate(override_ids):
                create_docs[index][BaseConstants.KEY] = override_id
        created_docs = self.db.upsert_many(create_docs)
        return [doc[BaseConstants.KEY] for doc in created_docs]  #  type: ignore

    def delete(self, id: str) -> bool:
        try:
            return self.db.delete(id)
        except DocumentDeleteError:
            raise EntityNotFound(collection=self.collection.value, entity_id=id)

    def get_one(self, **kwargs) -> DataSchema:
        query = ArangoDBRepository(self.request_scope.db, self.collection.value)
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
            db=self.request_scope.db,
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
            db=self.request_scope.db,
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

    def get_all(
        self, page: int = 0, page_size: int | None = None, **kwargs
    ) -> list[DataSchema]:
        pagination_params = {"page": page}
        if page_size:
            pagination_params["page_size"] = page_size
        repo_filters = RepoFilterParams(pagination=Pagination(**pagination_params))
        response = build_and_execute_query(
            db=self.request_scope.db,
            collection_name=self.collection.value,
            repo_filters=repo_filters,
            search_fields=self.search_fields,
            data_model=self.entity_model,
            **kwargs,
        )
        if isinstance(response, int):
            return []
        results, _ = response
        return [format_to_schema(result, self.entity_model) for result in results]

    def get_count(
        self, repo_filters: RepoFilterParams | QueryFilterParams | None = None, **kwargs
    ) -> int:
        response = build_and_execute_query(
            db=self.request_scope.db,
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
        query = ArangoDBRepository(self.request_scope.db, self.collection.value)
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
        results = self.db.get_many(document_ids)
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
                BaseConstants.CREATED_AT: datetime.now().isoformat(),
                BaseConstants.UPDATED_AT: datetime.now().isoformat(),
                BaseConstants.CREATED_BY: self.request_scope.user_id,
                BaseConstants.UPDATED_BY: self.request_scope.user_id,
            }
            for create_data in create_list
        ]
        if override_ids:
            for index, override_id in enumerate(override_ids):
                create_docs[index][BaseConstants.KEY] = override_id

        try:
            created_docs = self.db.create_many(create_docs)
        except CreateManyInsertError:
            raise FailedToCreate(self.collection.value, None)
        return [doc[BaseConstants.KEY] for doc in created_docs]  # type: ignore

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
                BaseConstants.UPDATED_AT: datetime.now().isoformat(),
                BaseConstants.UPDATED_BY: self.request_scope.user_id,
                BaseConstants.KEY: key,
            }
            for key, update_data in updates_as_dict.items()
        ]
        self.db.update_many(update_docs)
        return True

    def delete_many(self, document_ids: list[str]) -> bool:
        self.db.delete_many(document_ids)
        return True

    def get_autocomplete(self, field: str, prefix: str) -> list[dict]:
        query = ArangoDBRepository(self.request_scope.db, self.collection.value)
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
        results = ArangoDBRepository(
            self.request_scope.db, self.collection.value
        ).execute_custom_statement(statement, bind_vars)
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
        results = ArangoDBRepository(
            self.request_scope.db, self.collection.value
        ).execute_custom_statement(statement, bind_vars)
        return format_to_schema(results[0], self.entity_model)

    def get_most_recent(self, **kwargs) -> DataSchema:
        repo_filters = RepoFilterParams(
            pagination=Pagination(page=0, page_size=1),
            sorts=[
                Sort(
                    collection_alias="doc",
                    field=BaseConstants.CREATED_AT,
                    direction="DESC",
                )
            ],
        )
        results, _ = self.query(repo_filters=repo_filters, **kwargs)
        if len(results) == 0:
            raise EntityNotFound(collection=self.collection.value)
        return results[0]

    def get_oldest(self, **kwargs) -> DataSchema:
        repo_filters = RepoFilterParams(
            pagination=Pagination(page=0, page_size=1),
            sorts=[
                Sort(
                    collection_alias="doc",
                    field=BaseConstants.CREATED_AT,
                    direction="ASC",
                )
            ],
        )
        results, _ = self.query(repo_filters=repo_filters, **kwargs)
        if len(results) == 0:
            raise EntityNotFound(collection=self.collection.value)
        return results[0]

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

    def delete_all_children(self, parent_id: str) -> bool:
        """
        Ooofie this is a tough method name...
        When a parent record is deleted, this will delete all of the
        children records that are associated with it.
        """
        raise NotImplementedError


def check_if_parent_exists(
    db: StandardDatabase | TransactionDatabase, parent_collection: str, parent_id: str
) -> None:
    try:
        assert db.collection(parent_collection).get(parent_id)
    except AssertionError:
        raise EntityNotFound(collection=parent_collection, entity_id=parent_id)


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
        check_if_parent_exists(self.request_scope.db, parent_collection, parent_id)

    @staticmethod
    def _format_child_key(parent_collection: str, parent_id: str) -> str:
        return f"{parent_collection}_{parent_id}"

    def get_sub_entity(self) -> DataSchema:
        return self.get(self._format_child_key(self.parent_collection, self.parent_id))

    def set_sub_entity(self, data: CreateDataSchema) -> DataSchema:
        return self.upsert(
            data,
            overridden_id=self._format_child_key(
                self.parent_collection, self.parent_id
            ),
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
            check_if_parent_exists(self.request_scope.db, parent_collection, parent_id)
        else:
            warn(
                f"No parent id provided for {parent_collection}, parent document may not exist"
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
        query = ArangoDBRepository(self.db, self.view.value)
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
