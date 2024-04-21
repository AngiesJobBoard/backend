"""
This is responsible for creating and using transformation models to accept incoming data from all kinds of sources and shapes.

We will store the transformation model in JSON indicating which keys build the object we are trying to create.

Here is an example:

incoming_payload: {
    first_name: "John",
    last_name: "Doe",
}

expected_data_model: {
name: "John Doe"
}

transformation_model: {
    name: ["first_name", "last_name"]
}
"""

from pydantic import BaseModel
from typing import List
from jsonpath_ng import parse, JSONPath


class TransformerField(BaseModel):
    transformation_strings: List[str]
    output_path: str


class Transformer(BaseModel):
    fields: List[TransformerField]

    def transform(self, payload: dict) -> dict:
        transformed_payload = {}
        for field in self.fields:
            values = []
            for expression in field.transformation_strings:
                jsonpath_expr: JSONPath = parse(expression)
                matches = jsonpath_expr.find(payload)
                if matches:
                    values.append(matches[0].value)
                else:
                    values.append("")
            concatenated_value = " ".join(values).strip()

            # Create or update the path in transformed_payload
            output_jsonpath_expr = parse(field.output_path)
            self.set_value_by_path(
                transformed_payload, output_jsonpath_expr, concatenated_value
            )

        return transformed_payload

    def set_value_by_path(self, data, path, value_to_set):
        parts = str(path).split(".")[1:]
        for part in parts[:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        data[parts[-1]] = value_to_set
        return data


from ajb.base import BaseUseCase, RequestScope
from ajb.vendor.openai.repository import OpenAIRepository


class AITransformerModelUseCase(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, openai: OpenAIRepository | None = None
    ):
        self.request_scope = request_scope
        self.openai = openai or OpenAIRepository()

    def generate_application_transformer_from_example_payloads(
        self, incoming_payload: dict, expected_payload: dict
    ) -> Transformer:
        prompt = f"""
        You are given 2 JSON payloads and your job is to create the transformation model that converts one JSON into the other.
        You will do this by creating a list of pairs of JSONPath expressions that will be used to create the output JSON.
        Some fields may require multiple JSONPath expressions to be concatenated.
        The contexts of the 2 JSON payloads should be similiar so do your best to match the fields.
        First Payload: {incoming_payload}
        Second Payload: {expected_payload}
        """
        return self.openai.structured_prompt(prompt, Transformer)  # type: ignore


# from ajb.vendor.arango.repository import get_arango_db

# request_scope = RequestScope(user_id="test", db=get_arango_db(), company_id=None)
# t_repo = AITransformerModelUseCase(request_scope)


# output = t_repo.generate_application_transformer_from_example_payloads(
#     incoming_payload={
#         "first_name": "John",
#         "contact_info": {"nesty": {"last_name": "Doe"}},
#     },
#     expected_payload={"personal_info": {"name": "John Doe"}},
# )


# output.transform({
#         "first_name": "Bob",
#         "contact_info": {"nesty": {"last_name": "Ross"}},
#     })
