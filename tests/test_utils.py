from enum import Enum
from datetime import datetime
import unittest
from pydantic import BaseModel

from ajb.helpers.http import modify_query_parameters_in_url
from ajb.utils import (
    generate_random_short_code,
    string_to_bool,
    get_value_from_enum,
    update_dict,
    initialize_or_cast,
    replace_variables_in_html,
    closest_string_enum_match,
    get_datetime_from_string,
    get_miles_between_lat_long_pairs,
)


def test_generate_random_short_code():
    assert len(generate_random_short_code()) == 10


def test_string_to_bool():
    assert string_to_bool("True") is True
    assert string_to_bool("False") is False
    assert string_to_bool("true") is True
    assert string_to_bool("false") is False
    assert string_to_bool("foo") is False
    assert string_to_bool(None) is False


class ExampleEnum(Enum):
    ONE = 1
    TWO = "two"


class TestGetValueFromEnum(unittest.TestCase):
    def test_valid_member_name(self):
        self.assertEqual(get_value_from_enum("ONE", ExampleEnum), ExampleEnum.ONE)

    def test_valid_member_value_string(self):
        self.assertEqual(get_value_from_enum("two", ExampleEnum), ExampleEnum.TWO)

    def test_invalid_member_name(self):
        self.assertIsNone(get_value_from_enum("THREE", ExampleEnum))

    def test_case_sensitivity(self):
        # If case sensitivity matters, you can test it as well
        self.assertIsNone(get_value_from_enum("one", ExampleEnum))


class TestUpdateDict(unittest.TestCase):
    def test_both_dicts_are_empty(self):
        self.assertEqual(update_dict({}, {}), {})

    def test_d_is_none(self):
        self.assertEqual(update_dict(None, {"a": 1}), {"a": 1})  # type: ignore

    def test_simple_merge(self):
        d = {"a": 1}
        u = {"b": 2}
        self.assertEqual(update_dict(d, u), {"a": 1, "b": 2})

    def test_nested_dict_merge(self):
        d = {"a": {"b": 1}}
        u = {"a": {"c": 2}}
        self.assertEqual(update_dict(d, u), {"a": {"b": 1, "c": 2}})

    def test_list_merge_without_none(self):
        d = {"a": [1, 2]}
        u = {"a": [3, 4]}
        self.assertEqual(update_dict(d, u), {"a": [3, 4]})

    def test_list_merge_with_none(self):
        d = {"a": [1, 2]}
        u = {"a": [None, 4]}
        self.assertEqual(update_dict(d, u), {"a": [1, 4]})

    def test_mixed_structure(self):
        d = {"a": [1, 2], "b": {"c": 3}}
        u = {"a": [None, 4], "b": {"d": 5}}
        self.assertEqual(update_dict(d, u), {"a": [1, 4], "b": {"c": 3, "d": 5}})

    def test_u_has_none_value(self):
        d = {"a": 1}
        u = {"a": None}
        self.assertEqual(update_dict(d, u), {"a": 1})

    def test_d_has_none_value(self):
        d = {"a": None}
        u = {"a": 1}
        self.assertEqual(update_dict(d, u), {"a": 1})

    def test_u_is_empty(self):
        d = {"a": 1}
        u = {}
        self.assertEqual(update_dict(d, u), {"a": 1})


class TestReplaceVariablesInHtml(unittest.TestCase):
    html_content = "<h1>Hello, {{ name }}!</h1>"

    def test_replace_variables_in_html(self):
        variable_dict = {"name": "John"}
        result = replace_variables_in_html(self.html_content, variable_dict)
        self.assertEqual(result, "<h1>Hello, John!</h1>")

    def test_replace_variables_in_html_multiple(self):
        html_content = "<h1>Hello, {{ name }}!</h1><p>Welcome to {{ place }}.</p>"
        variable_dict = {"name": "John", "place": "Earth"}
        result = replace_variables_in_html(html_content, variable_dict)
        self.assertEqual(result, "<h1>Hello, John!</h1><p>Welcome to Earth.</p>")

    def test_replace_variables_in_html_no_match(self):
        variable_dict = {"another_name": "John"}
        result = replace_variables_in_html(self.html_content, variable_dict)
        self.assertEqual(result, self.html_content)


class TestEnum(Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"
    VALUE3 = "value3"


class TestClosestStringEnumMatch(unittest.TestCase):
    def test_closest_string_enum_match(self):
        input_string = "value1"
        result = closest_string_enum_match(input_string, TestEnum)
        self.assertEqual(result, "value1")

    def test_closest_string_enum_match_no_match(self):
        input_string = "nonexistent"
        result = closest_string_enum_match(input_string, TestEnum, cutoff=1)
        self.assertIsNone(result)


class TestModel(BaseModel):
    id: int
    name: str


class TestInitializeOrCast(unittest.TestCase):
    def test_initialize_or_cast_with_dict(self):
        data = {"id": 1, "name": "Test"}
        result = initialize_or_cast(TestModel, data)
        self.assertIsInstance(result, TestModel)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "Test")

    def test_initialize_or_cast_with_model_instance(self):
        data = TestModel(id=2, name="Test2")
        result = initialize_or_cast(TestModel, data)
        self.assertIsInstance(result, TestModel)
        self.assertEqual(result.id, 2)
        self.assertEqual(result.name, "Test2")


def test_modify_query_parameters_in_url():
    url = "https://example.com?param1=value1&param2=value2"
    new_params = {"param2": "newvalue2", "param3": "value3"}
    expected_url = "https://example.com?param1=value1&param2=newvalue2&param3=value3"
    assert modify_query_parameters_in_url(url, new_params) == expected_url


def test_get_datetime_from_string():
    test_dates = [
        "2024-03-12T15:29:45",
        "March 12, 2024 15:29:45",
        "12-03-2024",
        "15:29:45 12 March 2024",
        "dec 2024",
        "december, 2024",
        "2024 december",
    ]
    for date in test_dates:
        assert get_datetime_from_string(date) is not None
        assert isinstance(get_datetime_from_string(date), datetime)


def test_get_miles_between_lat_long_pairs():
    lat_long_pairs = [
        ((51.5074, 0.1278), (48.8566, 2.3522)),
        ((40.7128, -74.0060), (34.0522, -118.2437)),
        ((-33.8688, 151.2093), (35.6895, 139.6917)),
    ]
    for lat_long_pair in lat_long_pairs:
        assert (
            get_miles_between_lat_long_pairs(*lat_long_pair[0], *lat_long_pair[1]) > 0
        )
        assert isinstance(
            get_miles_between_lat_long_pairs(*lat_long_pair[0], *lat_long_pair[1]), int
        )

    distance = get_miles_between_lat_long_pairs(51.5074, 0.1278, 51.5074, 0.1278)
    assert distance == 0

    distance = get_miles_between_lat_long_pairs(50, 10, 50, 0)
    assert distance == 714
