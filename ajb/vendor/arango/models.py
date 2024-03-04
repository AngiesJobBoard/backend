import typing as t
from enum import Enum

from pydantic import BaseModel


class Operator(str, Enum):
    EQUALS = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_EQUAL = ">="
    LESS_THAN_EQUAL = "<="

    # IN and ARRAY_IN behave differently

    # IN will take a value like "one" and look through an array in the database like ["one", "two"]
    # If any of the values in the array match (both the term and the value are lowercased), the document is returned

    # For the ARRAY_IN operator, you provide an array of values like [1, 2, 3]
    # And the database will return all documents where the field is an array and contains any of the values in the array
    # database {id: 1, name: "one"}, {id: 2, name: "two"}, {id: 3, name: "three"}
    # get with array_in [1, 2] will return {id: 1, name: "one"}, {id: 2, name: "two"}

    IN = "IN"
    NOT_IN = "NOT IN"
    ARRAY_IN = "ARRAY IN"

    # Special operators for text search
    STARTS_WITH = "STARTS WITH"
    ENDS_WITH = "ENDS WITH"
    CONTAINS = "CONTAINS"

    def is_text_search(self) -> bool:
        return self in [Operator.STARTS_WITH, Operator.ENDS_WITH, Operator.CONTAINS]
    
    def is_in_search(self) -> bool:
        return self in [Operator.IN, Operator.NOT_IN]

    def format_text_search(self, query: str) -> str:
        if self == Operator.STARTS_WITH:
            return f"{query}%"
        if self == Operator.ENDS_WITH:
            return f"%{query}"
        if self == Operator.CONTAINS:
            return f"%{query}%"
        raise ValueError(f"Operator {self} is not a text search operator")

    @classmethod
    def from_query_string(cls, query_string: str):
        return {
            "eq": Operator.EQUALS,
            "ne": Operator.NOT_EQUAL,
            "gt": Operator.GREATER_THAN,
            "lt": Operator.LESS_THAN,
            "gte": Operator.GREATER_THAN_EQUAL,
            "lte": Operator.LESS_THAN_EQUAL,
            "in": Operator.IN,
            "notin": Operator.NOT_IN,
            "startswith": Operator.STARTS_WITH,
            "endswith": Operator.ENDS_WITH,
            "contains": Operator.CONTAINS,
        }[query_string]


class Filter(BaseModel):
    collection_alias: str = "doc"
    field: str
    operator: Operator = Operator.EQUALS
    value: t.Any
    and_or_operator: t.Literal["AND", "OR"] = "AND"

    @property
    def operator_value(self):
        return "LIKE" if self.operator.is_text_search() else self.operator.value

    @property
    def search_value(self):
        return (
            self.operator.format_text_search(self.value)
            if self.operator.is_text_search()
            else self.value
        )


class TextSearch(BaseModel):
    field: str
    query: str
    analyzer: str = "text_en"


class Sort(BaseModel):
    field: str
    direction: t.Literal["ASC", "DESC"] = "DESC"
    collection_alias: str = "doc"


class Join(BaseModel):
    """
    Example usage of a join with this model
    FOR user in users:
        FOR height in user_heights:
            FILTER user._id == height.user_id
            RETURN MERGE({ user, {height: height} })

    FOR from_collection_alias in (initial table set by repository):
        FOR to_collection_alias in to_collection:
            FILTER from_collection_alias.from_collection_join_attr == to_collection_alias.to_collection_join_attr
            RETURN MERGE({ from_collection_alias, {to_collection_alias: to_collection_alias} })

    If instead of returning all documents as a flat result, you can nest results using the is_aggregate
    This works the same as a group_by operation in SQL. The result will be a list of documents with the
    nested documents in an array.
    """

    to_collection_alias: str
    to_collection: str
    from_collection_alias: str = "doc"
    from_collection_join_attr: str
    to_collection_join_attr: str = "_key"
    is_aggregate: bool = False
