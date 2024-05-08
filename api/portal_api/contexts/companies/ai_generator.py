from fastapi import APIRouter, Body, UploadFile, File

from ajb.contexts.companies.job_generator.ai_generator import (
    AIJobGenerator,
)
from ajb.contexts.companies.job_generator.models import (
    GenerateQualifications,
    GenerateQuestions,
)
from ajb.contexts.companies.jobs.models import UserCreateJob
from ajb.common.models import PreferredTone
from ajb.vendor.pdf_plumber import extract_text, BadFileTypeException

from api.exceptions import GenericHTTPException
from api.vendors import openai


router = APIRouter(
    tags=["AI Company Job Generator"], prefix="/companies/{company_id}/job-generator"
)


@router.post("/job-from-description", response_model=UserCreateJob)
def generate_job_from_description(description: str = Body(...)):
    return AIJobGenerator(openai).generate_job_from_description(description)


@router.post("/job-from-url")
def create_job_from_url(url: str = Body(...)):
    return AIJobGenerator(openai).generate_job_from_url(url)


@router.post("/description-from-job")
def generate_description_from_job(
    job: UserCreateJob,
    tone: PreferredTone = Body(...),
):
    return AIJobGenerator(openai).generate_description_from_job_details(job, tone)


@router.post("/job-from-file")
async def create_job_from_file(file: UploadFile = File(...)):
    generator = AIJobGenerator(openai)
    try:
        extracted_text = await extract_text(file)
    except BadFileTypeException:
        raise GenericHTTPException(
            status_code=400,
            detail="The file type is not supported. Please upload a .docx, .pdf, or .txt file.",
        )
    return generator.generate_job_from_extracted_text(extracted_text)


@router.post("/improve-description")
def generate_improved_job_description(
    description: str = Body(...),
    tone: PreferredTone = Body(...),
):
    return AIJobGenerator(openai).generate_improved_job_description_from_draft(
        description, tone
    )


@router.post("/recommend-qualifications", response_model=GenerateQualifications)
def recommend_qualifications(job: UserCreateJob):
    return AIJobGenerator().recommend_qualifications(job)


@router.post("/recommend-questions", response_model=GenerateQuestions)
def recommend_questions_for_applicants(job: UserCreateJob):
    return AIJobGenerator(openai).recommend_questions_for_applicants(job)
