from ajb.base import Pagination, QueryFilterParams, RepoFilterParams
from ajb.vendor.arango.models import Sort, Filter, Operator


def test_basic_convert_query_to_repo_filters():
    example_query = QueryFilterParams(
        page=0,
        page_size=10,
        sorts="-id",
        filters="id=1,name=test",
        search="test",
    )
    converted_query = example_query.convert_to_repo_filters()
    expected_repo_query = RepoFilterParams(
        pagination=Pagination(page=0, page_size=10),
        sorts=[Sort(field="id", direction="DESC")],
        filters=[
            Filter(field="id", operator=Operator.EQUALS, value="1"),
            Filter(field="name", operator=Operator.EQUALS, value="test"),
        ],
        search_filters=[
            Filter(
                field="id",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            )
        ],
    )
    assert converted_query == expected_repo_query


def test_complicated_convert_queries():
    example_query = QueryFilterParams(
        page=10,
        page_size=100,
        sorts="-id,name",
        filters=(
            "sauce=boss,id__eq=1,id__ne=2,id__gt=3,id__gte=4,id__lt=5,id__lte=6,"
            "name__contains=test,name__startswith=test,name__endswith=test,"
            "person__id__eq=1,table__join__table__join__very__long__table__join__id__eq=1"
        ),
        search="test",
    )
    converted_query = example_query.convert_to_repo_filters()
    expected_query = RepoFilterParams(
        pagination=Pagination(page=10, page_size=100),
        sorts=[
            Sort(field="id", direction="DESC"),
            Sort(field="name", direction="ASC"),
        ],
        filters=[
            Filter(field="sauce", operator=Operator.EQUALS, value="boss"),
            Filter(field="id", operator=Operator.EQUALS, value="1"),
            Filter(field="id", operator=Operator.NOT_EQUAL, value="2"),
            Filter(field="id", operator=Operator.GREATER_THAN, value="3"),
            Filter(field="id", operator=Operator.GREATER_THAN_EQUAL, value="4"),
            Filter(field="id", operator=Operator.LESS_THAN, value="5"),
            Filter(field="id", operator=Operator.LESS_THAN_EQUAL, value="6"),
            Filter(field="name", operator=Operator.CONTAINS, value="test"),
            Filter(field="name", operator=Operator.STARTS_WITH, value="test"),
            Filter(field="name", operator=Operator.ENDS_WITH, value="test"),
            Filter(
                field="id",
                operator=Operator.EQUALS,
                value="1",
                collection_alias="person",
            ),
            Filter(
                field="join.table.join.very.long.table.join.id",
                operator=Operator.EQUALS,
                value="1",
                collection_alias="table",
            ),
        ],
        search_filters=[
            Filter(
                field="id",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
        ],
    )
    assert converted_query == expected_query


def test_multiple_search_fields():
    example_query = QueryFilterParams(
        search="test",
    )
    converted_query = example_query.convert_to_repo_filters(
        search_fields=("id", "name", "this", "that", "the", "other")
    )
    expected_query = RepoFilterParams(
        search_filters=[
            Filter(
                field="id",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
            Filter(
                field="name",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
            Filter(
                field="this",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
            Filter(
                field="that",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
            Filter(
                field="the",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
            Filter(
                field="other",
                operator=Operator.CONTAINS,
                value="test",
                and_or_operator="OR",
            ),
        ],
    )
    assert converted_query == expected_query
