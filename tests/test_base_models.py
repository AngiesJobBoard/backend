import pytest
from ajb.base.models import (
    RequestScope,
    build_pagination_response,
    PaginatedResponse,
)


def test_cannot_start_transaction_inside_transaction(request_scope: RequestScope):
    with request_scope.start_transaction(
        read_collections=[], write_collections=[]
    ) as transaction_scope:
        with pytest.raises(ValueError):
            with transaction_scope.start_transaction(
                read_collections=[], write_collections=[]
            ) as _:
                return True


def test_paginated_response_class():
    response = build_pagination_response(
        data_and_count=([1, 2, 3], 3), page=1, page_size=25, url="https://test.com"
    )
    assert response == PaginatedResponse(
        data=[1, 2, 3],  # type: ignore
        total=3,
        next="https://test.com?page=2&page_size=25",
        prev="https://test.com?page=0&page_size=25",
    )
