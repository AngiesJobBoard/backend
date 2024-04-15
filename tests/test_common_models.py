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
    assert abs(pay.min_pay_as_hourly - 12.5) < 1e-8
    assert pay.max_pay_as_hourly == 25
