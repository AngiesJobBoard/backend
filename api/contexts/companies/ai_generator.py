from fastapi import APIRouter, Request, Body, UploadFile, File
from pydantic import BaseModel

from ajb.contexts.companies.job_generator.ai_generator import (
    AIJobGenerator,
)
from ajb.contexts.companies.jobs.models import UserCreateJob
from ajb.common.models import PreferredTone
from ajb.vendor.pdf_plumber import extract_text, BadFileTypeException

from api.exceptions import GenericHTTPException
from api.vendors import openai, mixpanel


router = APIRouter(
    tags=["AI Company Job Generator"], prefix="/companies/{company_id}/job-generator"
)


@router.post("/job-from-description", response_model=UserCreateJob)
def generate_job_from_description(
    request: Request, company_id: str, description: str = Body(...)
):
    results = AIJobGenerator(openai).generate_job_from_description(description)
    mixpanel.job_description_is_generated(
        request.state.request_scope.user_id, company_id, "job_from_description"
    )
    return results


@router.post("/job-from-url")
def create_job_from_url(request: Request, company_id: str, url: str = Body(...)):
    results = AIJobGenerator(openai).generate_job_from_url(url)
    mixpanel.job_description_is_generated(
        request.state.request_scope.user_id, company_id, "job_from_url"
    )
    return results


@router.post("/description-from-job")
def generate_description_from_job(
    request: Request,
    company_id: str,
    job: UserCreateJob,
    tone: PreferredTone = Body(...),
):
    results = AIJobGenerator(openai).generate_description_from_job_details(job, tone)
    mixpanel.job_description_is_generated(
        request.state.request_scope.user_id, company_id, "description_from_job"
    )
    return results


@router.post("/job-from-file")
async def create_job_from_file(
    request: Request, company_id: str, file: UploadFile = File(...)
):
    generator = AIJobGenerator(openai)
    try:
        extracted_text = await extract_text(file)
    except BadFileTypeException:
        raise GenericHTTPException(
            status_code=400,
            detail="The file type is not supported. Please upload a .docx, .pdf, or .txt file.",
        )
    results = generator.generate_job_from_extracted_text(extracted_text)
    mixpanel.job_description_is_generated(
        request.state.request_scope.user_id, company_id, "job_from_file"
    )
    return results


@router.post("/improve-description")
def generate_improved_job_description(
    request: Request,
    company_id: str,
    description: str = Body(...),
    tone: PreferredTone = Body(...),
):
    results = AIJobGenerator(openai).generate_improved_job_description_from_draft(
        description, tone
    )
    mixpanel.job_description_is_generated(
        request.state.request_scope.user_id, company_id, "improved_description"
    )
    return results
