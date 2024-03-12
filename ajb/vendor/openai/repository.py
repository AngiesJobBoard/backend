import json
from openai import OpenAI
from aiohttp import ClientSession

from ajb.config.settings import SETTINGS
from ajb.vendor.openai.client_factory import OpenAIClientFactory


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


class AsyncOpenAIRepository:
    def __init__(self, async_session: ClientSession):
        self.async_session = async_session
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SETTINGS.OPENAI_API_KEY}",
        }

    async def _send_request(self, data: dict) -> dict:
        data["model"] = SETTINGS.OPENAI_MODEL
        # data["temperature"] = 0.7
        async with self.async_session.post(
            self.url, json=data, headers=self.headers
        ) as response:
            # response.raise_for_status()
            return await response.json()

    async def text_prompt(self, prompt: str, max_tokens: int = 100) -> str:
        data = {
            "messages": [{"role": "assistant", "content": prompt}],
            "max_tokens": max_tokens,
        }
        response = await self._send_request(data)
        return response["choices"][0]["message"]["content"]

    async def json_prompt(self, prompt: str, max_tokens: int = 100) -> dict:
        data = {
            "messages": [
                {
                    "role": "assistant",
                    "content": prompt,
                }
            ],
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        response = await self._send_request(data)
        return json.loads(response["choices"][0]["message"]["content"])
