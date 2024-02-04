from ajb.vendor.openai.repository import OpenAIRepository
from ajb.vendor.openai.client_factory import OpenAIClientFactory


def test_openai():
    mock = OpenAIClientFactory._return_mock()
    assert OpenAIRepository(mock).text_prompt(prompt="This is a test prompt")  # type: ignore
    assert OpenAIRepository(mock).json_prompt(prompt="This would be an example json prompt")  # type: ignore
