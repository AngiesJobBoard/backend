from ajb.common.models import PreferredTone
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.common.models import ExperienceLevel, JobLocationType
from ajb.contexts.companies.jobs.models import UserCreateJob


class AIJobGenerator:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository()

    def _convert_ai_response_to_job(self, response: dict) -> UserCreateJob:
        skills = []
        if response.get("required_job_skills"):
            skills = (
                response.get("required_job_skills", "").split(",")
                if isinstance(response.get("required_job_skills"), str)
                else response.get("required_job_skills")
            )

        licenses = []
        if response.get("license_requirements"):
            licenses = (
                response.get("license_requirements", "").split(",")
                if isinstance(response.get("license_requirements"), str)
                else response.get("license_requirements")
            )

        certifications = []
        if response.get("certification_requirements"):
            certifications = (
                response.get("certification_requirements", "").split(",")
                if isinstance(response.get("certification_requirements"), str)
                else response.get("certification_requirements")
            )

        created_job = UserCreateJob(
            position_title=response.get("position_title", "").title(),
            description=response.get("description"),
            required_job_skills=skills,
            industry_category=response.get("industry_category", ""),
            industry_subcategories=response.get("industry_subcategories"),
            license_requirements=licenses,
            certification_requirements=certifications,
        )
        return created_job

    def generate_job_from_description(
        self,
        description: str,
    ) -> UserCreateJob:
        job_keys = [
            "position_title",
            "industry_category",
            "industry_subcategories",
            "required_job_skills",
            "description",
            "license_requirements",
            "certification_requirements",
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
        return self._convert_ai_response_to_job(response)

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
                Description: {draft}",
            max_tokens=4096,
        )

    def generate_job_from_url(self, url: str) -> UserCreateJob:
        job_keys = [
            "position_title",
            "industry_category",
            "industry_subcategories",
            "required_job_skills",
            "description",
            "license_requirements",
            "certification_requirements",
        ]
        response = self.openai.json_prompt(
            prompt=f"""
            Given the following URL which represents a job post, create a job with the following keys.
            Do your best to provide some answer for each key. Respond only in JSON format.
            Keys: {job_keys}.
            URL: {url}.
            """,
            max_tokens=4096,
        )
        return self._convert_ai_response_to_job(response)
