from ajb.common.models import PreferredTone
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.common.models import ExperienceLevel, JobLocationType
from ajb.contexts.companies.jobs.models import UserCreateJob


class AIJobGenerator:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository()

    def generate_job_from_description(
        self,
        description: str,
        preferred_tone: PreferredTone = PreferredTone.professional,
    ) -> UserCreateJob:
        job_keys = [
            "position_title as str",
            "industry_category as str",
            "industry_subcategories as list[str]",
            "required_job_skills as list[str]",
            f"description as str in the following tone: {preferred_tone.value}",
        ]
        response = self.openai.json_prompt(
            prompt=f"""
            You are an expert at defining jobs. Given the following job description, create a job with the following keys.
            Do your best to provide some answer for each key. Respond only in JSON format.
            Keys: {job_keys}.
            Job Description: {description}.
            """,
            max_tokens=4096,
        )
        created_job = UserCreateJob(
            position_title=response["position_title"].title(),
            description=response["description"],
            required_job_skills=response["required_job_skills"],
            industry_category=response["industry_category"],
            industry_subcategories=response["industry_subcategories"],
        )
        created_job.description = self.generate_improved_job_description_from_draft(
            description, tone=PreferredTone.professional
        )
        return created_job

    def generate_description_from_job_details(
        self, job: UserCreateJob, tone: PreferredTone
    ) -> str:
        job_as_dict = {
            "position_title": job.position_title,
            "industry_category": job.industry_category,
            "industry_subcategories": job.industry_subcategories,
            "experience_required": (
                job.experience_required.value if job.experience_required else None
            ),
            "required_job_skills": job.required_job_skills,
            "location_type": job.location_type.value if job.location_type else None,
        }
        # Remove null values from dict
        job_as_dict = {k: v for k, v in job_as_dict.items() if v is not None}
        return self.openai.text_prompt(
            prompt=f"""
            Given the following job details,
            write a long job description with the following tone: {tone.value}.
            {job_as_dict}
            """,
            max_tokens=2000,
        )

    def generate_improved_job_description_from_draft(
        self, draft: str, tone: PreferredTone
    ):
        return self.openai.text_prompt(
            prompt=f"Given the following job description, \
                write a better and much longer job description in the following tone: {tone.value}. \
                Description: {draft}"
        )
