import time
from enum import Enum
from unittest.mock import patch
import pytest
from pydantic import BaseModel
from arango.database import StandardDatabase

from ajb.base import (
    BaseViewRepository,
    ParentRepository,
    BaseDataModel,
    RepoFilterParams,
)
from ajb.exceptions import EntityNotFound
from ajb.vendor.arango.models import Filter, Operator


@pytest.fixture(scope="function")
def view_setup(db: StandardDatabase):
    db.create_collection("view_collection_1")
    db.create_collection("view_collection_2")

    db.create_view(
        name="view_1",
        view_type="arangosearch",
        properties={
            "name": "view_1",
            "links": {
                "view_collection_1": {
                    "analyzers": ["identity"],
                    "fields": {},
                    "includeAllFields": True,
                    "storeValues": "none",
                    "trackListPositions": False,
                },
                "view_collection_2": {
                    "analyzers": ["identity"],
                    "fields": {},
                    "includeAllFields": True,
                    "storeValues": "none",
                    "trackListPositions": False,
                },
            },
        },
    )

    yield "view_collection_1", "view_collection_2", "view_1"

    db.delete_view("view_1")
    db.delete_collection("view_collection_1")
    db.delete_collection("view_collection_2")


class CreateModelOne(BaseModel):
    name: str


class ModelOne(CreateModelOne, BaseDataModel):
    ...


class CreateModelTwo(BaseModel):
    age: int


class ModelTwo(CreateModelTwo, BaseDataModel):
    ...


class TestCollection(str, Enum):
    view_collection_1 = "view_collection_1"
    view_collection_2 = "view_collection_2"


class TestView(str, Enum):
    view_1 = "view_1"


class RepositoryOne(ParentRepository[CreateModelOne, ModelOne]):
    collection = TestCollection.view_collection_1  # type: ignore
    entity_model = ModelOne


class RepositoryTwo(ParentRepository[CreateModelTwo, ModelTwo]):
    collection = TestCollection.view_collection_2  # type: ignore
    entity_model = ModelTwo


class ViewRepository(BaseViewRepository):
    view = TestView.view_1  # type: ignore


def test_basic_view_repository(view_setup, request_scope):
    repo_one = RepositoryOne(request_scope)
    repo_two = RepositoryTwo(request_scope)
    view_repo = ViewRepository(request_scope)

    repo_one.create(CreateModelOne(name="test"))
    repo_two.create(CreateModelTwo(age=10))

    time.sleep(1.5)  # Wait for view to be updated
    results, _ = view_repo.query()
    assert len(results) == 2


def test_view_repository_with_filters(view_setup, request_scope):
    repo_one = RepositoryOne(request_scope)
    repo_two = RepositoryTwo(request_scope)
    view_repo = ViewRepository(request_scope)

    created_1 = repo_one.create(CreateModelOne(name="test"))
    repo_two.create(CreateModelTwo(age=10))

    time.sleep(1.5)  # Wait for view to be updated
    results, _ = view_repo.query(
        repo_filters=RepoFilterParams(
            filters=[Filter(field="name", operator=Operator.EQUALS, value="test")]
        )
    )
    assert len(results) == 1
    assert results[0]["_key"] == created_1.id


def test_view_repository_get_one(view_setup, request_scope):
    repo_one = RepositoryOne(request_scope)
    repo_two = RepositoryTwo(request_scope)
    view_repo = ViewRepository(request_scope)

    created_1 = repo_one.create(CreateModelOne(name="test"))
    repo_two.create(CreateModelTwo(age=10))
    time.sleep(1.5)  # Wait for view to be updated

    res_1 = view_repo.get(created_1.id)
    assert res_1["_key"] == created_1.id


def test_view_not_found(view_setup, request_scope):
    repo_one = ViewRepository(request_scope)
    with pytest.raises(EntityNotFound):
        repo_one.get("not_found")


def test_incorrect_query_type(view_setup, request_scope):
    repo_one = ViewRepository(request_scope)

    with patch("ajb.base.repository.build_and_execute_query") as mock_query:
        mock_query.return_value = 1

        results = repo_one.query()
        assert results[0] == []
        assert results[1] == 1
