"""
This module is intended to take a PDF of a resume and extract the data from it.
"""

from pydantic import BaseModel
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.contexts.applications.models import WorkHistory, Education


class ExtractedResume(BaseModel):
    first_name: str | None
    last_name: str | None
    email: str | None
    phone_number: str | None
    most_recent_job_title: str | None
    most_recent_job_company: str | None
    skills: list[str] | None
    education: list[Education] | None
    work_experience: list[WorkHistory] | None
    certifications: list[str] | None
    licenses: list[str] | None
    languages: list[str] | None


class AIResumeExtractor:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository()

    def get_candidate_profile_from_resume_text(self, resume_text: str):
        results = self.openai.json_prompt(
            prompt=f"""
            This is a resume parser that will extract the following information from a resume and return it as a JSON object:
            - first_name as str
            - last_name as str
            - email as str
            - phone_number as str
            - most_recent_job_title as str
            - most_recent_job_company as str
            - skills as list[str]
            - education as list[dict[school_name as str, field_of_study as str, level_of_education as str, start_date as str, end_date as str]]
            - work_experience as list[dict[job_title as str, company_name as str, start_date as str, end_date as str]]
            - certifications as list[str]
            - licenses as list[str]
            - languages as list[str]

            Resume text: {resume_text}
            """,
            max_tokens=4000,
        )
        return ExtractedResume(**results)
