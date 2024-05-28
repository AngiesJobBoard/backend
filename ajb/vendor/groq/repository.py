import os
import json
from typing import Type
from pydantic import BaseModel
from instructor import from_groq
from groq import Groq

from ajb.config.settings import SETTINGS
from ajb.vendor.groq.client_factory import GroqClientFactory


class GroqRepository:
    def __init__(self, client: Groq | None = None, model_override: str | None = None):
        self.client = client or GroqClientFactory.get_client()
        self.instructor = from_groq(self.client)
        self.model_override = model_override

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
            model=self.model_override or SETTINGS.GROQ_LLAMA_MODEL,
            response_model=response_model,
            messages=messages,
            max_tokens=max_tokens,
        )

    def transcribe_audio(self, filepaths: list[str]):
        results = []
        for filepath in filepaths:
            full_path = os.path.join(os.path.dirname(__file__), filepath)
            with open(full_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(filepath, file.read()),
                    model=SETTINGS.GROQ_WHISPER_MODEL,
                )
                results.append(transcription.text)
        return results
