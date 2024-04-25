from ajb.common.models import PreferredTone
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.contexts.companies.jobs.models import UserCreateJob

from .models import GenerateQualifications, GenerateQuestions


class AIJobGenerator:
    def __init__(self, openai: OpenAIRepository | None = None):
        self.openai = openai or OpenAIRepository(model_override="gpt-4-turbo")
        self.generate_job_keys = [
            "position_title",
            "industry_category",
            "industry_subcategories",
            "description",
            "experience_required",
            "schedule",
        ]

    def generate_job_from_description(
        self,
        description: str,
    ):
        return self.openai.structured_prompt(
            prompt=f"""
            You are writing a job posting for a company. Given the following job 
            You are an expert at defining jobs. Given the following job description, create a job with the following keys.
            Do your best to provide some answer for each key. Respond only in JSON format.
            Only include the following Keys in your response: {self.generate_job_keys}.
            Job Description: {description}.
            """,
            max_tokens=4096,
            response_model=UserCreateJob,
        )

    def recommend_qualifications(self, job_data: UserCreateJob):
        return self.openai.structured_prompt(
            prompt=f"""
            Given the following details describing a job, recommend qualifications for the job.
            Return skills, licenses, and qualifications that are relevant to the job.
            Try to recommend up to 3 qualifications for each type and duplicate the 2 most important qualifications in both the selected and recommended lists.
            Job Details: {job_data.model_dump()}
            """,
            max_tokens=4096,
            response_model=GenerateQualifications,
        )

    def recommend_questions_for_applicants(self, job_data: UserCreateJob):
        return self.openai.structured_prompt(
            prompt=f"""
            Given the following job details, recommend questions that could be answered by looking only at an applicant's resume.
            These questions should be relevant to the job and help a recruiter understand the applicant's qualifications.
            Try to recommend up to 5 questions and duplicate the 2 most important questions in both the selected and recommended lists.
            All questions must have a yes or no answer. If a question can not be answered with yes or no, it should not be included.
            Job Details: {job_data.model_dump()}
            """,
            max_tokens=4096,
            response_model=GenerateQuestions,
        )

    def generate_description_from_job_details(
        self, job: UserCreateJob, tone: PreferredTone
    ) -> str:
        # Remove null values from dict
        job_as_dict = {k: v for k, v in job.model_dump().items() if v is not None}
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

    def generate_job_from_url(self, url: str):
        return self.openai.structured_prompt(
            prompt=f"""
            Given the following URL which represents a job post, create a job with the following keys.
            Do your best to provide some answer for each key. Respond only in JSON format.
            Only include the following Keys: {self.generate_job_keys}.
            URL: {url}.
            """,
            max_tokens=4096,
            response_model=UserCreateJob,
        )

    def generate_job_from_extracted_text(self, text: str):
        return self.openai.structured_prompt(
            prompt=f"""
            Given the following text which represents a job post, create a job with the following keys.
            Do your best to provide some answer for each key. Respond only in JSON format.
            Only include the following Keys: {self.generate_job_keys}.
            Text: {text}.
            """,
            max_tokens=4096,
            response_model=UserCreateJob,
        )
