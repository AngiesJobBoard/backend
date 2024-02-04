import json
from openai import OpenAI
from ajb.config.settings import SETTINGS

from .client_factory import OpenAIClientFactory


class OpenAIRepository:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or OpenAIClientFactory.get_client()

    def text_prompt(self, prompt: str, max_tokens: int = 100) -> str:
        response = self.client.chat.completions.create(
            model=SETTINGS.OPENAI_MODEL,
            messages=[{"role": "assistant", "content": prompt}],
            max_tokens=max_tokens,
        )
        output = response.choices[0].message.content
        if not output:
            raise ValueError("OpenAI returned an empty response")
        return output

    def json_prompt(self, prompt: str, max_tokens: int = 100) -> dict:
        response = self.client.chat.completions.create(
            model=SETTINGS.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "assistant", "content": prompt}],
            max_tokens=max_tokens,
        )
        output = response.choices[0].message.content
        if not output:
            raise ValueError("OpenAI returned an empty response")
        return json.loads(output)
