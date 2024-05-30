from typing import Optional

from pydantic import BaseModel

from ajb.contexts.applications.models import Application
from ajb.contexts.companies.jobs.models import Job
from ajb.vendor.openai.repository import OpenAIRepository

from .models import CreateInterviewQuestions


class AIJobDetails(BaseModel):
    position_title: str
    description: str
    industry_category: str
    industry_subcategories: list[str]
    experience_required: Optional[str]
    required_job_skills: list[str]
    license_requirements: list[str]
    certification_requirements: list[str]
    language_requirements: list[str]


class AIApplicationDetails(BaseModel):
    most_recent_job: Optional[str]
    most_recent_industry: Optional[str]
    previous_jobs: Optional[list[str]]
    work_industries: Optional[list[str]]
    skills: Optional[list[str]]
    licenses: Optional[list[str]]
    certifications: Optional[list[str]]
    languages: Optional[list[str]]


class AIJobInterviewQuestions:
    def __init__(self, openai: OpenAIRepository | None = None) -> None:
        self.openai = openai or OpenAIRepository(model_override="gpt-4o")

    def make_prompt(
        self, ai_job_data: AIJobDetails, ai_application_data: AIApplicationDetails
    ):
        intro = "Generate a suite of tailored interview questions based on the provided APPLICANT DETAILS and JOB DETAILS."
        outro = "Use the APPLICANT DETAILS and JOB DETAILS to generate more specific and relevant questions, ensuring they address the key points mentioned in both documents."
        user_prompt = f"""
        {intro}

        **APPLICANT DETAILS:**
        
        MOST RECENT JOB: {ai_application_data.most_recent_job}
        MOST RECENT INDUSTRY: {ai_application_data.most_recent_industry}
        PREVIOUS JOBS: {ai_application_data.previous_jobs}
        WORK INDUSTRIES: {ai_application_data.work_industries}
        SKILLS: {ai_application_data.skills}
        LICENSES: {ai_application_data.licenses}
        CERTIFICATIONS: {ai_application_data.certifications}
        LANGUAGES: {ai_application_data.languages}

        **JOB DETAILS:**

        POSITION TITLE: {ai_job_data.position_title}
        DESCRIPTION: {ai_job_data.description}
        INDUSTRY CATEGORY: {ai_job_data.industry_category}
        INDUSTRY SUBCATEGORIES: {ai_job_data.industry_subcategories}
        EXPERIENCE REQUIRED: {ai_job_data.experience_required}
        REQUIRED JOB SKILLS: {ai_job_data.required_job_skills}
        LICENSE REQUIREMENTS: {ai_job_data.license_requirements}
        CERTIFICATION REQUIREMENTS: {ai_job_data.certification_requirements}
        LANGUAGE REQUIREMENTS: {ai_job_data.language_requirements}

        {outro}
        """
        return user_prompt

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

    def _get_applicant_details(self, application: Application) -> AIApplicationDetails:
        qualifications = application.qualifications
        if not qualifications:
            return AIApplicationDetails()

        return AIApplicationDetails(
            most_recent_job=(
                qualifications.most_recent_job.job_title
                if qualifications.most_recent_job
                else None
            ),
            most_recent_industry=(
                qualifications.most_recent_job.job_industry
                if qualifications.most_recent_job
                else None
            ),
            previous_jobs=(
                [job.job_title for job in qualifications.work_history]
                if qualifications.work_history
                else None
            ),
            work_industries=(
                [job.job_industry for job in qualifications.work_history]
                if qualifications.work_history
                else None
            ),
            skills=qualifications.skills,
            licenses=qualifications.licenses,
            certifications=qualifications.certifications,
            languages=(
                qualifications.language_proficiencies
                if qualifications.language_proficiencies
                else None
            ),
        )

    def generate_interview_questions(
        self, *, job: Job, application: Application
    ) -> CreateInterviewQuestions:
        job_details = self._get_job_details(job)
        applicant_details = self._get_applicant_details(application)
        system_prompt = """
        You are a perfect at assisting an interviewer with generating insightful questions. Using the given APPLICANT DETAILS and JOB DETAILS, generate a suite of tailored interview questions that assess the interviewee's qualifications, experiences, and skills relevant to the job. Ensure the questions are comprehensive and cover different aspects.
        """
        return self.openai.structured_prompt(
            prompt=self.make_prompt(job_details, applicant_details),
            response_model=CreateInterviewQuestions,
            max_tokens=4000,
            system_prompt=system_prompt,
        )
