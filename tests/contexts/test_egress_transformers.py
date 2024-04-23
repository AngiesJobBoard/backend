from ajb.contexts.webhooks.ingress.applicants.transformers.usecase import (
    Transformer,
    TransformerField,
)


def test_transformer():
    example_transformer = Transformer(
        fields=[
            TransformerField(
                transformation_strings=[
                    "$.first_name",
                    "$.contact_info.nesty.last_name",
                ],
                output_path="$.personal_info.name",
            )
        ]
    )

    example_incoming_payload = {
        "first_name": "John",
        "contact_info": {"nesty": {"last_name": "Doe"}},
    }

    # Convert incoming payloads
    converted_payload = example_transformer.transform(example_incoming_payload)
    assert converted_payload == {"personal_info": {"name": "John Doe"}}
