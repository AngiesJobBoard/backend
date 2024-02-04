"""
Provided a draft cover letter text and basic details about a job, 
this will return an improved version of the cover letter
"""

from ajb.common.models import PreferredTone
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.contexts.companies.jobs.models import Job


class AICoverLetterGenerator:
    def __init__(
        self,
        openai: OpenAIRepository | None = None,
    ):
        self.openai = openai or OpenAIRepository()

    def _get_job_details_as_dict(self, job: Job):
        return {
            "position_title": job.position_title,
            "description": job.description,
            "industry_category": job.industry_category,
            "required_job_skills": job.required_job_skills,
        }

    def generate_cover_letter_from_draft(
        self,
        draft: str,
        job: Job,
        tone: PreferredTone,
    ) -> str:
        job_details = self._get_job_details_as_dict(job)
        return self.openai.text_prompt(
            prompt=f"""
            Given the following job details and a draft cover letter,
            return an improved version of the cover letter that is truthful
            and uses the tone {tone.value}.
            Job details: {job_details}.
            Draft: {draft}.
            """,
            max_tokens=2000,
        )
