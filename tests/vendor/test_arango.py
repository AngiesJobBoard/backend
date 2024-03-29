import pytest
from arango.database import StandardDatabase

from ajb.vendor.arango.repository import ArangoDBRepository
from ajb.vendor.arango.models import (
    Filter,
    Sort,
    Operator,
    Join,
)


@pytest.fixture(scope="session", autouse=True)
def create_collection(db: StandardDatabase):
    db.create_collection("test")
    yield "test"
    db.delete_collection("test")


@pytest.fixture(scope="function")
def join_collections(db: StandardDatabase):
    db.create_collection("join_one")
    db.create_collection("join_two")
    yield "join_one", "join_two"
    db.delete_collection("join_one")
    db.delete_collection("join_two")


@pytest.fixture(scope="function")
def collection(db: StandardDatabase):
    db.collection("test").truncate()
    yield "test"


def test_basic_query(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    assert db.collection(collection).count() == 1

    query = ArangoDBRepository(db, collection)
    results, count = query.execute()
    assert count == 1
    assert any(result["test"] == "test" for result in results)


def test_basic_filter(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.EQUALS, value="test"))
    results, count = query.execute()
    assert count == 1
    assert any(result["test"] == "test" for result in results)


def test_basic_sort(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test", "created_at": 1})
    db.collection(collection).insert({"test": "great", "created_at": 2})

    # Default sort is desc creation date
    query = ArangoDBRepository(db, collection)
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == "great"

    query = ArangoDBRepository(db, collection)
    query.add_sort(Sort(field="test", direction="ASC"))
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == "great"
    assert results[1]["test"] == "test"

    query = ArangoDBRepository(db, collection)
    query.add_sort(Sort(field="test", direction="DESC"))
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == "test"
    assert results[1]["test"] == "great"


def test_basic_pagination(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test", "created_at": 1})
    db.collection(collection).insert({"test": "great", "created_at": 2})

    query = ArangoDBRepository(db, collection)
    query.set_pagination(offset=0, limit=1)
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == "great"

    query = ArangoDBRepository(db, collection)
    query.set_pagination(offset=1, limit=1)
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == "test"


def test_equal_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.EQUALS, value="test"))
    results, count = query.execute()
    assert count == 1
    assert results[0]["test"] == "test"


def test_not_equal_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.NOT_EQUAL, value="test"))
    results, count = query.execute()
    assert count == 1
    assert results[0]["test"] == "great"


def test_greater_than_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": 1})
    db.collection(collection).insert({"test": 2})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.GREATER_THAN, value=1))
    results, count = query.execute()
    assert count == 1
    assert results[0]["test"] == 2


def test_less_than_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": 1})
    db.collection(collection).insert({"test": 2})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.LESS_THAN, value=2))
    results, count = query.execute()
    assert count == 1
    assert results[0]["test"] == 1


def test_greater_than_equal_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": 1, "created_at": 1})
    db.collection(collection).insert({"test": 2, "created_at": 2})

    query = ArangoDBRepository(db, collection)
    query.add_filter(
        Filter(field="test", operator=Operator.GREATER_THAN_EQUAL, value=1)
    )
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == 2
    assert results[1]["test"] == 1


def test_less_than_equal_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": 1, "created_at": 1})
    db.collection(collection).insert({"test": 2, "created_at": 2})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.LESS_THAN_EQUAL, value=2))
    results, count = query.execute()
    assert count == 2
    assert results[0]["test"] == 2
    assert results[1]["test"] == 1


def test_array_in_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})
    db.collection(collection).insert({"test": "test2"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(
        Filter(field="test", operator=Operator.ARRAY_IN, value=["test", "test2"])
    )
    results, count = query.execute()
    assert count == 2
    assert any(result["test"] == "test" for result in results)
    assert any(result["test"] == "test2" for result in results)


def test_in_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": ["Test", "this"]})
    db.collection(collection).insert({"test": ["Great", "results"]})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.IN, value="test"))
    results, _ = query.execute()

    # AJBTODO count is broken for this operator
    assert len(results) == 1
    assert results[0]["test"] == ["Test", "this"]


# AJBTODO this operator is broken
# def test_not_in_operator(db: StandardDatabase, collection: str):
#     db.collection(collection).insert({"test": ["Test", "this"]})
#     db.collection(collection).insert({"test": ["Great", "results"]})

#     query = ArangoDBRepository(db, collection)
#     query.add_filter(Filter(field="test", operator=Operator.NOT_IN, value="test"))
#     results, count = query.execute()

#     # AJBTODO count is broken for this operator
#     assert len(results) == 1
#     assert results[0]["test"] == ["Great", "results"]


def test_contains_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})
    db.collection(collection).insert({"test": "test2"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.CONTAINS, value="test%"))
    results, count = query.execute()
    assert count == 2
    assert any(result["test"] == "test" for result in results)
    assert any(result["test"] == "test2" for result in results)


def test_starts_with_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})
    db.collection(collection).insert({"test": "test2"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.STARTS_WITH, value="test"))
    results, count = query.execute()
    assert count == 2
    assert any(result["test"] == "test" for result in results)
    assert any(result["test"] == "test2" for result in results)


def test_ends_with_operator(db: StandardDatabase, collection: str):
    db.collection(collection).insert({"test": "test"})
    db.collection(collection).insert({"test": "great"})
    db.collection(collection).insert({"test": "test2"})

    query = ArangoDBRepository(db, collection)
    query.add_filter(Filter(field="test", operator=Operator.ENDS_WITH, value="test"))
    results, count = query.execute()
    assert count == 1
    assert any(result["test"] == "test" for result in results)


def test_bad_operator():
    with pytest.raises(ValueError):
        Filter(field="test", operator="bad", value="test")  # type: ignore


def test_bad_search_operator():
    with pytest.raises(ValueError):
        Operator.EQUALS.format_text_search("test")


def test_basic_query_with_join(db: StandardDatabase, join_collections):
    coll_1, coll_2 = join_collections
    db.collection(coll_1).insert({"_key": "one", "name": "Bob"})
    db.collection(coll_2).insert({"user_id": "one", "height": 500})

    query = ArangoDBRepository(db, coll_1)
    query.add_join(
        Join(
            to_collection_alias="user_height",
            to_collection=coll_2,
            to_collection_join_attr="user_id",
            from_collection_join_attr="_key",
        )
    )
    results, count = query.execute()
    assert results[0]["name"] == "Bob"
    assert results[0]["user_height"]["height"] == 500


def test_query_with_joins_and_filters(db: StandardDatabase, join_collections):
    coll_1, coll_2 = join_collections
    db.collection(coll_1).insert({"_key": "one", "name": "Bob"})
    db.collection(coll_1).insert({"_key": "two", "name": "Sally"})
    db.collection(coll_2).insert({"user_id": "one", "height": 500})
    db.collection(coll_2).insert({"user_id": "two", "height": 1000})

    query = ArangoDBRepository(db, coll_1)
    query.add_join(
        Join(
            to_collection_alias="user_height",
            to_collection=coll_2,
            to_collection_join_attr="user_id",
            from_collection_join_attr="_key",
        )
    )
    query.add_filter(
        Filter(
            collection_alias="user_height",
            field="height",
            operator=Operator.GREATER_THAN,
            value=600,
        )
    )
    results, count = query.execute()
    assert results[0]["name"] == "Sally"
    assert results[0]["user_height"]["height"] == 1000


def test_get_with_join(db: StandardDatabase, join_collections):
    coll_1, coll_2 = join_collections
    db.collection(coll_1).insert({"_key": "one", "name": "Bob"})
    db.collection(coll_1).insert({"_key": "two", "name": "Sally"})
    db.collection(coll_2).insert({"user_id": "one", "height": 500})
    db.collection(coll_2).insert({"user_id": "two", "height": 1000})

    query = ArangoDBRepository(db, coll_1)
    query.add_join(
        Join(
            to_collection_alias="user_height",
            to_collection=coll_2,
            to_collection_join_attr="user_id",
            from_collection_join_attr="_key",
        )
    )
    query.return_single_document("one")
    results, count = query.execute()
    assert count == 1
    assert results[0]["name"] == "Bob"
    assert results[0]["user_height"]["height"] == 500


def test_search(db: StandardDatabase, collection: str):
    db.collection(collection).insert(
        {"test": "test", "text_two": "monkey", "is_cool": True}
    )
    db.collection(collection).insert(
        {"test": "great", "text_two": "monkey", "is_cool": False}
    )

    query = ArangoDBRepository(db, collection)
    query.add_search_filter(
        Filter(field="test", operator=Operator.CONTAINS, value="test")
    )
    results, count = query.execute()
    assert count == 1
    assert results[0]["test"] == "test"

    query = ArangoDBRepository(db, collection)
    query.add_search_filter(
        Filter(field="test", operator=Operator.CONTAINS, value="monkey")
    )
    query.add_search_filter(
        Filter(field="text_two", operator=Operator.CONTAINS, value="monkey")
    )
    results, count = query.execute()
    assert count == 2

    query = ArangoDBRepository(db, collection)
    query.add_search_filter(
        Filter(field="test", operator=Operator.CONTAINS, value="monkey")
    )
    query.add_search_filter(
        Filter(field="text_two", operator=Operator.CONTAINS, value="monkey")
    )
    query.add_filter(Filter(field="is_cool", operator=Operator.EQUALS, value=True))
    results, count = query.execute()
    assert count == 1
    assert results[0]["test"] == "test"
