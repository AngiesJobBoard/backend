"""
This module will take the data from a job and provide a score based on
the quality of the job posting.
Quality is based on the completeness of the job posting and the
likliehood that the job posting will attract qualified candidates.
"""

from pydantic import BaseModel
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.contexts.companies.jobs.models import CreateJob


class JobScore(BaseModel):
    job_score: int
    job_score_reason: str


class AIJobScore:
    def __init__(self, openai: OpenAIRepository):
        self.openai = openai

    def _get_job_details(self, job: CreateJob):
        return {
            "position_title": job.position_title,
            "description": job.description,
            "industry_category": job.industry_category,
            "industry_subcategories": job.industry_subcategories,
            "experience_required": (
                job.experience_required.value if job.experience_required else None
            ),
            "required_job_skills": job.required_job_skills,
            "license_requirements": job.license_requirements,
            "certification_requirements": job.certification_requirements,
            "language_requirements": job.language_requirements,
        }

    def get_job_score(self, job: CreateJob):
        results = self.openai.json_prompt(
            f"""
            You are an experting at creating the best job postings to find the most qualified candidates.
            Given the following details about a job posting, return a score from 0 to 100 that represents the quality of the job posting. Try to not round to the nearest 10.
            This should be based on the completeness of the posting and the likliehood that the posting will attract many qualified candidates.
            Return a JSON object with the following keys:
            - job_score: int
            - job_score_reason: str
            job: {self._get_job_details(job)}
            """,
            max_tokens=3000
        )
        return JobScore(**results)
