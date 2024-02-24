import typing as t
import os
import importlib
from uuid import uuid4
import string
from enum import Enum
import secrets
import collections.abc
import difflib
from pydantic import BaseModel


def initialize_repositories():
    # Import all repositores so that they are registered in the repository registry
    print("Initializing repositories")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for dirpath, _, filenames in os.walk(os.path.join(current_dir, "contexts")):
        if "repository.py" in filenames:
            module_name = (
                os.path.join(dirpath, "repository")
                .replace("/", ".")
                .replace("\\", ".")
                .replace(".py", "")
            )
            index = module_name.find("ajb")
            if index != -1:
                module_name = module_name[index:]
            importlib.import_module(module_name)  # type: ignore
    print("Repositories initialized")


def generate_random_short_code(length: int = 10):
    return "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length)
    )


def generate_random_long_code():
    return str(uuid4())


def string_to_bool(string_in: str | None = None) -> bool:
    if string_in is None:
        return False
    if string_in.lower() == "true":
        return True
    return False


def replace_variables_in_html(html_content: str, variable_dict: dict):
    """
    Replaces variables in an HTML string with the values in a dictionary if they match a {{ variable_name }} pattern.
    """
    for key, value in variable_dict.items():
        html_content = html_content.replace("{{ " + key + " }}", str(value))
    return html_content


def get_value_from_enum(value: str, enumeration: t.Type[Enum]):
    """
    Returns the value from an enumeration.
    """
    if value in enumeration.__members__:
        return enumeration.__members__[value]
    if value in enumeration._value2member_map_:
        return enumeration._value2member_map_[value]
    return None


def update_dict(
    d: dict[t.Any, t.Any] | None, u: dict[t.Any, t.Any]
) -> dict[t.Any, t.Any]:
    """
    Recursively updates dictionary 'd' with values from dictionary 'u'.
    If 'd' is None, it initializes it with 'u'.
    Utilizes helper functions for handling specific types of updates.
    """
    if d is None:
        return u.copy()

    for key, value in u.items():
        if isinstance(value, collections.abc.Mapping):
            d[key] = update_nested_dict(d.get(key, {}), value)  # type: ignore
        elif isinstance(value, list):
            d[key] = merge_lists(d.get(key, []), value)
        else:
            d[key] = value if value is not None else d.get(key)

    return d


def update_nested_dict(
    original: dict[t.Any, t.Any], new: dict[t.Any, t.Any]
) -> dict[t.Any, t.Any]:
    """
    Recursively updates a nested dictionary with values from another dictionary.
    """
    return update_dict(original, new)


def merge_lists(original: list, new: list) -> list:
    """
    Merges two lists, using elements from 'new' unless they are None,
    in which case it preserves the corresponding element from 'original'.
    """
    return [
        new_value if new_value is not None else original[idx]
        for idx, new_value in enumerate(new)
    ]


def closest_string_enum_match(
    input_string: str,
    enumeration: t.Type[Enum],
    cutoff: float = 0.0,
) -> str | None:
    """
    Returns the closest matching string from the enumeration.
    """
    matches = difflib.get_close_matches(
        input_string, [e.value for e in enumeration.__members__.values()], cutoff=cutoff
    )

    if not matches:
        return None

    return matches[0]


def initialize_or_cast(model_to_cast: t.Type[BaseModel], data: t.Any) -> t.Any:
    if isinstance(data, dict):
        return model_to_cast(**data)
    return t.cast(model_to_cast, data)  # type: ignore


def get_nested_value(dictionary, keys, default=None):
    """
    Safely get a nested value from a dictionary.
    :param dictionary: The dictionary to search.
    :param keys: A list of keys for nested access.
    :param default: The default value to return if any key is not found.
    :return: The value from the nested dictionary or the default value.
    """
    current_level = dictionary
    for key in keys:
        if current_level is None:
            return default
        current_level = current_level.get(key, None)
    return current_level if current_level is not None else default


def get_perecent(numerator: int, denominator: int) -> int:
    if denominator == 0:
        return 0
    return round((numerator / denominator) * 100)
