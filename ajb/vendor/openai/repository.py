import json
from typing import Type
from pydantic import BaseModel
from instructor import from_openai
from openai import OpenAI
from aiohttp import ClientSession

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
        self,
        prompt: str,
        response_model: Type[BaseModel],
        max_tokens: int = 100,
        system_prompt: str | None = None,
    ):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return self.instructor.chat.completions.create(
            model=self.model_override or SETTINGS.OPENAI_MODEL,
            response_model=response_model,
            messages=messages,
            max_tokens=max_tokens,
        )


class AsyncOpenAIRepository:
    def __init__(self, async_session: ClientSession, model_override: str | None = None):
        self.async_session = async_session
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SETTINGS.OPENAI_API_KEY}",
        }
        self.model_override = model_override

    async def _send_request(self, data: dict) -> dict:
        data["model"] = self.model_override or SETTINGS.OPENAI_MODEL
        async with self.async_session.post(
            self.url, json=data, headers=self.headers
        ) as response:
            # response.raise_for_status()
            return await response.json()

    async def text_prompt(self, prompt: str, max_tokens: int = 100) -> str:
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        response = await self._send_request(data)
        if "choices" not in response or not response["choices"]:
            raise ValueError(f"OpenAI returned an empty response: {response}")
        return response["choices"][0]["message"]["content"]

    async def json_prompt(self, prompt: str, max_tokens: int = 100) -> dict:
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        response = await self._send_request(data)
        if "choices" not in response or not response["choices"]:
            raise ValueError(f"OpenAI returned an empty response: {response}")
        return json.loads(response["choices"][0]["message"]["content"])
