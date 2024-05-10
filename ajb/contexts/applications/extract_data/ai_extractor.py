"""
This module is intended to take a PDF of a resume and extract the data from it.
"""

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
    This is a resume parser that will extract the following information from a resume and return it as a JSON object:
    - first_name as str
    - last_name as str
    - email as str
    - phone_number as str
    - city as str
    - state as str
    - most_recent_job_title as str
    - most_recent_job_company as str
    - skills as list[str]
    - education as list[dict[school_name as str, field_of_study as str, level_of_education as str, start_date as str, end_date as str]]
    - work_experience as list[dict[job_title as str, company_name as str, start_date as str, end_date as str]]
    - certifications as list[str]
    - licenses as list[str]
    - languages as list[str]

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


class AIResumeExtractor:
    def __init__(self, openai: AsyncOpenAIRepository):
        self.openai = openai

    async def get_candidate_profile_from_resume_text(self, resume_text: str):
        if resume_text == "":
            raise EmptyResumeException
        results = await self.openai.json_prompt(
            prompt=generate_prompt(resume_text),
            max_tokens=4000,
        )
        return ExtractedResume(**results)
