import pytest

from ajb.common.models import (
    convert_pay_to_hourly,
    Pay,
    PayType,
)


def test_convert_pay_to_hourly():
    assert convert_pay_to_hourly(100, PayType.HOURLY) == 100
    assert convert_pay_to_hourly(800, PayType.DAILY) == 100
    assert convert_pay_to_hourly(4000, PayType.WEEKLY) == 100
    assert convert_pay_to_hourly(16000, PayType.MONTHLY) == 100
    assert convert_pay_to_hourly(208000, PayType.YEARLY) == 100

    with pytest.raises(ValueError):
        convert_pay_to_hourly(100, "INVALID_PAY_TYPE")  # type: ignore


def test_pay_with_conversion():
    pay = Pay(pay_type=PayType.DAILY, pay_min=100, pay_max=200)
    assert pay.min_pay_as_hourly == 12.5
    assert pay.max_pay_as_hourly == 25


# AJBTODO write new test cases for the location class
# def test_general_location_gets_lat_lon():
#     general_location_without_latlon = Location(
#         city="New York", state="NY", country="USA"
#     )
#     assert general_location_without_latlon.get_google_string() == "New York NY USA"
#     assert general_location_without_latlon.lat is not None
#     assert general_location_without_latlon.lng is not None


# def test_location_gets_lat_lon():
#     location = Location(
#         address_line_1="123 Main St",
#         city="New York",
#         state="NY",
#         zipcode="10001",
#         country="USA",
#     )
#     assert location.get_google_string() == "123 Main St New York NY 10001 USA"
#     assert location.lat is not None
#     assert location.lng is not None
