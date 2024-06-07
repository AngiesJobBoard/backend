"""
This module will take an application and provide a match score
based on qualifications of the candidate and the requirements of the job posting.
"""

from pydantic import BaseModel
from ajb.vendor.openai.repository import AsyncOpenAIRepository
from ajb.contexts.applications.models import Application
from ajb.contexts.companies.jobs.models import Job


class ApplicantMatchScore(BaseModel):
    match_score: int
    match_reason: str


class AIApplicationMatcher:
    def __init__(self, openai: AsyncOpenAIRepository):
        self.openai = openai

    def _get_job_details(self, job: Job):
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

    async def get_match_score(
        self, application: Application, job: Job
    ) -> ApplicantMatchScore:
        return await self.openai.structured_prompt(
            f"""
            You are an expert at matching applicants to job postings.
            Given the following job details, description, and user resume text,
            return a match score between 0 and 100 for how good of a fit the applicant is for the job. Try to not round to the nearest 10.
            Return a JSON object with the following keys:
            - match_score (int between 0 and 100)
            - match_reason (str)
            job: {self._get_job_details(job)}
            applicant resume: {application.extracted_resume_text}
            """,
            max_tokens=3000,
            response_model=ApplicantMatchScore,
        )
