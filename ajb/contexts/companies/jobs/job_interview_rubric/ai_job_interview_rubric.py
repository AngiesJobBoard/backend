from typing import List, Optional

from pydantic import BaseModel

from ajb.contexts.companies.jobs.models import Job
from ajb.vendor.openai.repository import OpenAIRepository
from .models import CreateJobInterviewRubric


class AIJobDetails(BaseModel):
    position_title: str
    description: str
    industry_category: str
    industry_subcategories: List[str]
    experience_required: Optional[str]
    required_job_skills: List[str]
    license_requirements: List[str]
    certification_requirements: List[str]
    language_requirements: List[str]


class AIJobInterviewRubric:
    def __init__(self, openai: OpenAIRepository | None = None) -> None:
        self.openai = openai or OpenAIRepository(model_override="gpt-4o")

    def make_prompt_v1(self, ai_job_data: AIJobDetails):
        intro = "You are tasked with creating a grading rubric for evaluating a candidate's interview transcript based on the given job description."
        prompt = f"""{intro}
        \n\nPOSITION TITLE: {ai_job_data.position_title}
        \n\nDESCRIPTION: {ai_job_data.description}
        """
        return prompt

    def make_prompt_v2(self, ai_job_data: AIJobDetails):
        intro = "You are tasked with creating a grading rubric for evaluating a candidate's interview transcript based on the given job description."
        prompt = f"""{intro}
        \n\nPOSITION TITLE: {ai_job_data.position_title}
        \n\nDESCRIPTION: {ai_job_data.description}
        \n\nINDUSTRY CATEGORY: {ai_job_data.industry_category}
        \n\nINDUSTRY SUBCATEGORIES: {ai_job_data.industry_subcategories}
        \n\nEXPERIENCE REQUIRED: {ai_job_data.experience_required}
        \n\nREQUIRED JOB SKILLS: {ai_job_data.required_job_skills}
        \n\nLICENSE REQUIREMENTS: {ai_job_data.license_requirements}
        \n\nCERTIFICATION REQUIREMENTS: {ai_job_data.certification_requirements}
        \n\nLANGUAGE REQUIREMENTS: {ai_job_data.language_requirements}
        """
        return prompt

    def _get_job_details(self, job: Job) -> AIJobDetails:
        job_details = AIJobDetails(
            position_title=job.position_title or "No position title",
            description=job.description or "No description",
            industry_category=job.industry_category or "No industry category",
            industry_subcategories=job.industry_subcategories
            or ["No industry subcategories"],
            experience_required=(
                job.experience_required.value
                if job.experience_required
                else "No experience required"
            ),
            required_job_skills=job.required_job_skills or ["No required job skills"],
            license_requirements=job.license_requirements
            or ["No license requirements"],
            certification_requirements=job.certification_requirements
            or ["No certification requirements"],
            language_requirements=job.language_requirements
            or ["No language requirements"],
        )
        return job_details

    def generate_job_rubric(self, job: Job) -> CreateJobInterviewRubric:
        job_details = self._get_job_details(job)
        return self.openai.structured_prompt(
            prompt=self.make_prompt_v1(job_details),
            response_model=CreateJobInterviewRubric,
            max_tokens=20000,
        )
