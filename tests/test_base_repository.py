from unittest.mock import patch
import pytest
from pydantic import BaseModel
from arango.exceptions import DocumentGetError

from ajb.exceptions import EntityNotFound, MultipleEntitiesReturned
from ajb.base import (
    ParentRepository,
    SingleChildRepository,
    MultipleChildrenRepository,
    RequestScope,
    BaseDataModel,
    Collection,
    RepoFilterParams,
    QueryFilterParams,
)
from ajb.base.repository import format_child_key
from ajb.vendor.arango.models import Filter, Sort, Operator


class CreateTestModel(BaseModel):
    name: str | None = None
    age: int | None = None
    is_cool: bool | None = None
    text_one: str | None = None
    text_two: str | None = None
    text_three: str | None = None


class TestModel(BaseDataModel, CreateTestModel): ...


class TestRepository(ParentRepository[CreateTestModel, TestModel]):
    collection = Collection.ADMIN_USERS
    entity_model = TestModel


class BasicSearchTestRepository(ParentRepository[CreateTestModel, TestModel]):
    collection = Collection.ADMIN_USERS
    entity_model = TestModel
    search_fields = ("name",)


class ManySearchTestRepository(ParentRepository[CreateTestModel, TestModel]):
    collection = Collection.ADMIN_USERS
    entity_model = TestModel
    search_fields = ("name", "text_one", "text_two", "text_three")


def test_basic_repository_actions(request_scope: RequestScope):
    repo = TestRepository(request_scope)

    # Create
    data = CreateTestModel(name="test", age=1, is_cool=True)
    result = repo.create(data)
    assert result.name == "test"

    # Get
    result = repo.get(result.id)

    # Get one
    result = repo.get_one(name="test")
    assert result.name == "test"

    # Update
    data = CreateTestModel(name="test2", age=2, is_cool=False)
    result = repo.update(result.id, data)
    assert result.name == "test2"

    # Partial update
    data = CreateTestModel(name="test3")
    result = repo.update(result.id, data)
    assert result.name == "test3"

    # Make sure other fields are not updated
    result = repo.get(result.id)
    assert result.age == 2
    assert result.is_cool is False

    # Update Field
    result = repo.update_fields(result.id, name="test3")
    assert result.name == "test3"

    # Check that other fields are not updated
    result = repo.get(result.id)
    assert result.age == 2

    # Delete
    repo.delete(result.id)

    # Multiple create
    data_to_create = [
        CreateTestModel(name="test", age=idx, is_cool=True) for idx in range(10)
    ]
    created_ids = repo.create_many(data_to_create)

    # Multiple get
    repo.get_many_by_id(created_ids)

    # Multiple update as dict
    updated_data = {created_id: {"is_cool": False} for created_id in created_ids}
    updated_success = repo.update_many(updated_data)  # type: ignore
    assert updated_success

    all_items = repo.get_many_by_id(created_ids)
    assert all(item.is_cool is False for item in all_items if item)
    assert all(item.name == "test" for item in all_items if item)

    # Multiple update as model
    updated_data = {
        created_id: CreateTestModel(is_cool=True) for created_id in created_ids  # type: ignore
    }
    updated_success = repo.update_many(updated_data)  # type: ignore
    assert updated_success

    all_items = repo.get_many_by_id(created_ids)
    assert all(item.is_cool is True for item in all_items if item)
    assert all(item.name == "test" for item in all_items if item)

    # Multiple delete
    repo.delete_many(created_ids)
    all_items = repo.get_many_by_id(created_ids)
    assert len(all_items) == 0

    # Not found errors
    with pytest.raises(EntityNotFound):
        repo.get("not_found")

    with pytest.raises(EntityNotFound):
        repo.update("not_found", CreateTestModel(name="test"))

    with pytest.raises(EntityNotFound):
        repo.update_fields("not_found", name="test")

    with pytest.raises(EntityNotFound):
        repo.delete("not_found")


def test_arango_document_get_error(request_scope):
    repo = TestRepository(request_scope)
    with patch("arango.database.Database.collection") as mock_collection:
        mock_collection.get.side_effect = DocumentGetError
        with pytest.raises(EntityNotFound):
            repo.get("not_found")


def test_repository_queries(request_scope: RequestScope):
    repo = TestRepository(request_scope)

    # Create example records
    repo.create(CreateTestModel(name="test", age=1, is_cool=True))
    repo.create(CreateTestModel(name="test2", age=2, is_cool=False))
    repo.create(CreateTestModel(name="test3", age=3, is_cool=True))
    repo.create(CreateTestModel(name="test4", age=4, is_cool=False))
    repo.create(CreateTestModel(name="test5", age=5, is_cool=True))

    # Basic Query
    results, count = repo.query()
    assert count == 5

    # Filter
    results, count = repo.query(
        repo_filters=RepoFilterParams(
            filters=[Filter(field="name", operator=Operator.EQUALS, value="test")]
        )
    )
    assert count == 1
    assert results[0].name == "test"

    # Filter with kwargs
    results, count = repo.query(name="test")
    assert count == 1
    assert results[0].name == "test"

    # Sort
    results, count = repo.query(
        repo_filters=RepoFilterParams(sorts=[Sort(field="age", direction="ASC")])
    )
    assert count == 5
    assert results[0].age == 1


def test_text_search(request_scope):
    # These all have the same collections so they share the same data
    repo = TestRepository(request_scope)
    basic_repo = BasicSearchTestRepository(request_scope)
    many_repo = ManySearchTestRepository(request_scope)

    # Create example records
    repo.create(
        CreateTestModel(
            name="test", age=1, text_one="pandas", text_two="pizza", text_three="bears"
        )
    )
    repo.create(
        CreateTestModel(
            name="test2",
            age=2,
            text_one="boats",
            text_two="motorcycle",
            text_three="jeans",
        )
    )
    repo.create(
        CreateTestModel(
            name="test3",
            age=3,
            text_one="pandas",
            text_two="motorcycle",
            text_three="jeans",
        )
    )
    repo.create(
        CreateTestModel(
            name="test4", age=4, text_one="boats", text_two="pizza", text_three="bears"
        )
    )

    query = QueryFilterParams(search="test")
    results, count = basic_repo.query(repo_filters=query)
    assert count == 4
    assert len(results) == 4

    query = QueryFilterParams(search="test2")
    results, count = basic_repo.query(repo_filters=query)
    assert count == 1
    assert len(results) == 1

    query = QueryFilterParams(search="test")
    results, count = many_repo.query(repo_filters=query)
    assert count == 4
    assert len(results) == 4

    query = QueryFilterParams(search="pandas")
    results, count = many_repo.query(repo_filters=query)
    assert count == 2
    assert len(results) == 2

    query = QueryFilterParams(search="motor")
    results, count = many_repo.query(repo_filters=query)
    assert count == 2
    assert len(results) == 2


def test_text_search_with_filters(request_scope):
    # These all have the same collections so they share the same data
    repo = TestRepository(request_scope)
    basic_repo = BasicSearchTestRepository(request_scope)
    many_repo = ManySearchTestRepository(request_scope)

    repo.create(
        CreateTestModel(
            name="test", age=1, text_one="pandas", text_two="pizza", text_three="bears"
        )
    )
    repo.create(
        CreateTestModel(
            name="test2",
            age=2,
            text_one="boats",
            text_two="motorcycle",
            text_three="jeans",
        )
    )
    repo.create(
        CreateTestModel(
            name="test3",
            age=3,
            text_one="pandas",
            text_two="motorcycle",
            text_three="jeans",
        )
    )
    repo.create(
        CreateTestModel(
            name="test4", age=4, text_one="boats", text_two="pizza", text_three="bears"
        )
    )

    query = QueryFilterParams(search="test", filters="age=2")
    results, count = basic_repo.query(repo_filters=query)
    assert count == 1
    assert len(results) == 1
    assert results[0].name == "test2"

    query = QueryFilterParams(search="test", filters="nonexistent_field=10")
    results, count = basic_repo.query(repo_filters=query)
    assert count == 0
    assert len(results) == 0

    query = QueryFilterParams(
        search="motor", filters="age__gt=1,text_three__endswith=eans"
    )
    results, count = many_repo.query(repo_filters=query)
    assert count == 2
    assert len(results) == 2

    query = QueryFilterParams(search="boats", filters="age=4")
    results, count = many_repo.query(repo_filters=query)
    assert count == 1
    assert results[0].name == "test4"

    query = QueryFilterParams(search="nonexistent", filters="age=5")
    results, count = basic_repo.query(repo_filters=query)
    assert count == 0
    assert len(results) == 0

    query = QueryFilterParams(search="PANDAS", filters="text_three__startswith=be")
    results, count = many_repo.query(repo_filters=query)
    assert count == 1

    query = QueryFilterParams(search="test", filters="age__gte=2,age__lt=4")
    results, count = many_repo.query(repo_filters=query)
    assert count == 2

    query = QueryFilterParams(search="jeans", filters="text_one=pandas,age__gt=1")
    results, count = many_repo.query(repo_filters=query)
    assert count == 1
    assert results[0].name == "test3"


def test_autocomplete(request_scope):
    repo = TestRepository(request_scope)
    repo.create(CreateTestModel(name="testone"))
    repo.create(CreateTestModel(name="testtwo"))
    repo.create(CreateTestModel(name="testthree"))

    result = repo.get_autocomplete(field="name", prefix="tes")
    assert len(result) == 3

    result = repo.get_autocomplete(field="name", prefix="testo")
    assert len(result) == 1

    result = repo.get_autocomplete(field="name", prefix="noexisto")
    assert len(result) == 0


def test_format_child_key():
    assert format_child_key("one", "two") == "one_two"


def test_multiple_returns(request_scope):
    repo = TestRepository(request_scope)
    repo.create(CreateTestModel(name="test"))
    repo.create(CreateTestModel(name="test"))

    with pytest.raises(MultipleEntitiesReturned):
        repo.get_one(name="test")


def test_bad_return_type_query(request_scope):
    repo = TestRepository(request_scope)

    with patch("ajb.base.repository.build_and_execute_query") as mock_query:
        mock_query.return_value = 1
        response = repo.query()
        assert response[0] == []
        assert response[1] == 1


def test_bad_return_type_when_querying_with_joins(request_scope):
    repo = TestRepository(request_scope)

    with patch("ajb.base.repository.build_and_execute_query") as mock_query:
        mock_query.return_value = 1
        response = repo.query_with_joins()
        assert response[0] == []
        assert response[1] == 1


def test_get_one_with_joins_multiple_returns(request_scope):
    repo = TestRepository(request_scope)
    repo.create(CreateTestModel(name="test"))
    repo.create(CreateTestModel(name="test"))

    with pytest.raises(MultipleEntitiesReturned):
        repo.get_one_with_joins(name="test")


def test_get_one_with_joins_none_found(request_scope):
    repo = TestRepository(request_scope)

    with pytest.raises(EntityNotFound):
        repo.get_one_with_joins(name="noexisto")


def test_get_count_non_integer_response(request_scope):
    repo = TestRepository(request_scope)

    with patch("ajb.base.repository.build_and_execute_query") as mock_query:
        mock_query.return_value = [], 1
        results = repo.get_count()
        assert results == 1


def test_get_with_joins_not_found(request_scope):
    repo = TestRepository(request_scope)

    with pytest.raises(EntityNotFound):
        repo.get_with_joins("not_found", joins=[])


def test_get_with_joins_no_model(request_scope):
    repo = TestRepository(request_scope)
    created_item = repo.create(CreateTestModel(name="test"))

    results = repo.get_with_joins(created_item.id, joins=[], return_model=None)
    assert results["_key"] == created_item.id


def test_create_many_with_unequal_override_id_list(request_scope):
    repo = TestRepository(request_scope)
    data = [CreateTestModel(name="test"), CreateTestModel(name="test2")]
    with pytest.raises(ValueError):
        repo.create_many(data, override_ids=["one"])


def test_create_many_with_equal_override_id_list(request_scope):
    repo = TestRepository(request_scope)
    data = [CreateTestModel(name="test"), CreateTestModel(name="test2")]
    results = repo.create_many(data, override_ids=["one", "two"])
    assert results == ["one", "two"]


class TestSingleChildRepository(SingleChildRepository[CreateTestModel, TestModel]):
    parent_collection = Collection.ADMIN_USERS
    collection = Collection.ADMIN_USERS
    entity_model = TestModel

    def __init__(self, request_scope: RequestScope, parent_id: str):
        super().__init__(request_scope, self.parent_collection, parent_id)


def test_single_child_repository(request_scope):
    parent_repo = TestRepository(request_scope)
    example_item = parent_repo.create(CreateTestModel(name="test"))

    child_repo = TestSingleChildRepository(request_scope, example_item.id)

    child_repo.set_sub_entity(CreateTestModel(name="test2"))
    child_repo.set_sub_entity(CreateTestModel(name="test3"))

    results = child_repo.get_sub_entity()
    assert results.name == "test3"


class TestMultipleChildRepository(
    MultipleChildrenRepository[CreateTestModel, TestModel]
):
    parent_collection = Collection.ADMIN_USERS
    collection = Collection.ADMIN_USERS
    entity_model = TestModel

    def __init__(self, request_scope: RequestScope, parent_id: str):
        super().__init__(request_scope, self.parent_collection, parent_id)


def test_multiple_child_repository(request_scope):
    parent_repo = TestRepository(request_scope)
    example_item = parent_repo.create(CreateTestModel(name="test"))

    child_repo = TestMultipleChildRepository(request_scope, example_item.id)
    child_repo.create(CreateTestModel(name="test2"), overridden_id="one")

    result = child_repo.get("one")
    assert result.name == "test2"


def test_increment_field(request_scope):
    parent_repo = TestRepository(request_scope)
    example_item = parent_repo.create(CreateTestModel(name="test", age=1))

    result = parent_repo.increment_field(example_item.id, "age", 1)
    assert result.age == 2

    queried_result = parent_repo.get(example_item.id)
    assert queried_result.age == 2

    big_result = parent_repo.increment_field(example_item.id, "age", 100)
    assert big_result.age == 102


def test_decrement_field(request_scope):
    parent_repo = TestRepository(request_scope)
    example_item = parent_repo.create(CreateTestModel(name="test", age=100))

    result = parent_repo.decrement_field(example_item.id, "age", 1)
    assert result.age == 99

    queried_result = parent_repo.get(example_item.id)
    assert queried_result.age == 99

    big_result = parent_repo.decrement_field(example_item.id, "age", 100)
    assert big_result.age == -1
