import json
from typing import Type, Any
from asyncio import get_event_loop
from pydantic import BaseModel
from instructor import from_openai
from openai import OpenAI

from ajb.config.settings import SETTINGS
from ajb.vendor.openai.client_factory import OpenAIClientFactory


class OpenAIRepository:
    def __init__(self, client: OpenAI | None = None, model_override: str | None = None):
        self.client = client or OpenAIClientFactory.get_client()
        self.instructor = from_openai(self.client)
        self.model_override = model_override

    def text_prompt(self, prompt: str, max_tokens: int = 100) -> str:
        response = self.client.chat.completions.create(
            model=self.model_override or SETTINGS.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        output = response.choices[0].message.content
        if not output:
            raise ValueError("OpenAI returned an empty response")
        return output

    def json_prompt(self, prompt: str, max_tokens: int = 100) -> dict:
        response = self.client.chat.completions.create(
            model=self.model_override or SETTINGS.OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        output = response.choices[0].message.content
        if not output:
            raise ValueError("OpenAI returned an empty response")
        return json.loads(output)

    def structured_prompt(
        self, prompt: str, response_model: Type[BaseModel], max_tokens: int = 100
    ):
        return self.instructor.chat.completions.create(
            model=self.model_override or SETTINGS.OPENAI_MODEL,
            response_model=response_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )


class AsyncOpenAIRepository:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository()

    async def text_prompt(self, prompt: str, max_tokens: int = 100) -> str:
        loop = get_event_loop()
        result = await loop.run_in_executor(
            None, self.openai.text_prompt, prompt, max_tokens
        )
        return result

    async def json_prompt(self, prompt: str, max_tokens: int = 100) -> dict:
        loop = get_event_loop()
        result = await loop.run_in_executor(
            None, self.openai.json_prompt, prompt, max_tokens
        )
        return result

    async def structured_prompt(
        self, prompt: str, response_model: Type[BaseModel], max_tokens: int = 100
    ) -> Any:
        loop = get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.openai.structured_prompt,
            prompt,
            response_model,
            max_tokens,
        )
        return result
