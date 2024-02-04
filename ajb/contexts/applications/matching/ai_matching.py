"""
This module will take an application and provide a match score
based on qualifications of the candidate and the requirements of the job posting.
"""

from pydantic import BaseModel
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.contexts.users.models import User
from ajb.contexts.companies.jobs.models import Job


class ApplicantMatchScore(BaseModel):
    match_score: int
    match_reason: str


class AIApplicationMatcher:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository()

    def _get_applicant_qualifications(self, user: User):
        qualifications = user.qualifications
        job_preferences = user.job_preferences

        return {
            "most_recent_job": (
                qualifications.most_recent_job.job_title
                if qualifications.most_recent_job
                else None
            ),
            "most_recent_industry": (
                qualifications.most_recent_job.job_industry
                if qualifications.most_recent_job
                else None
            ),
            "previous_jobs": (
                [job.job_title for job in qualifications.work_history]
                if qualifications.work_history
                else None
            ),
            "work_industries": (
                [job.job_industry for job in qualifications.work_history]
                if qualifications.work_history
                else None
            ),
            "skills": qualifications.skills,
            "licenses": qualifications.licenses,
            "certifications": qualifications.certifications,
            "languages": (
                [
                    language.language
                    for language in qualifications.language_proficiencies
                ]
                if qualifications.language_proficiencies
                else None
            ),
            "desired_job_title": job_preferences.desired_job_title,
            "desired_pay": job_preferences.desired_pay,
            "desired_industry": job_preferences.desired_industries,
        }

    def _get_job_details(self, job: Job):
        return {
            "position_title": job.position_title,
            "description": job.description,
            "industry_category": job.industry_category,
            "industry_subcategories": job.industry_subcategories,
            "experience_required": (
                job.experience_required.value if job.experience_required else None
            ),
            "required_job_skills": (
                [skill.skill_name for skill in job.required_job_skills]
                if job.required_job_skills
                else None
            ),
            "license_requirements": job.license_requirements,
            "certification_requirements": job.certification_requirements,
            "language_requirements": job.language_requirements,
            "minimum_hourly_pay": job.pay.min_pay_as_hourly if job.pay else None,
        }

    def get_match_score(self, user: User, job: Job):
        results = self.openai.json_prompt(
            f"""
            Given the following job description and applicant qualifications,
            return a JSON object with the following keys:
            - match_score (int between 0 and 10)
            - match_reason (str)
            job: {self._get_job_details(job)}
            user: {self._get_applicant_qualifications(user)}
            """,
            max_tokens=3000,
        )
        return ApplicantMatchScore(
            match_score=results["match_score"],
            match_reason=results["match_reason"],
        )
