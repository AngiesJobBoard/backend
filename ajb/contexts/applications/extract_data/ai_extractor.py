"""
This module is intended to take a PDF of a resume and extract the data from it.
"""

import asyncio
from pydantic import BaseModel
from ajb.vendor.openai.repository import AsyncOpenAIRepository, OpenAIRepository
from ajb.contexts.applications.models import WorkHistory, Education


class ExtractedResume(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    city: str | None = None
    state: str | None = None
    most_recent_job_title: str | None = None
    most_recent_job_company: str | None = None
    skills: list[str] | None = None
    education: list[Education] | None = None
    work_experience: list[WorkHistory] | None = None
    certifications: list[str] | None = None
    licenses: list[str] | None = None
    languages: list[str] | None = None


def generate_prompt(resume_text: str) -> str:
    return f"""
    This is text that represents a resume, structured as follows:
    Resume text: {resume_text}
    """


class EmptyResumeException(Exception):
    pass


class SyncronousAIResumeExtractor:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository()

    def get_candidate_profile_from_resume_text(self, resume_text: str):
        if resume_text == "":
            raise EmptyResumeException
        return self.openai.structured_prompt(
            prompt=generate_prompt(resume_text),
            max_tokens=4000,
            response_model=ExtractedResume,
        )


openai = OpenAIRepository()


class AIResumeExtractor:
    def __init__(self, openai: AsyncOpenAIRepository):
        self.openai = openai

    async def get_candidate_profile_from_resume_text(self, resume_text: str):
        if resume_text == "":
            raise EmptyResumeException

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            openai.structured_prompt,
            generate_prompt(resume_text),
            ExtractedResume,
            4000,
        )
        return result
