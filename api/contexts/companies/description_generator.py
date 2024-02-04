from fastapi import APIRouter, Request, Depends, Body

from ajb.contexts.companies.job_generator.ai_generator import AIJobGenerator
from ajb.contexts.companies.jobs.models import UserCreateJob
from ajb.common.models import PreferredTone

from api.vendors import openai


router = APIRouter(
    tags=["AI Company Job Generator"], prefix="/companies/{company_id}/job-generator"
)


@router.post("/job-from-description", response_model=UserCreateJob)
def generate_job_from_description(company_id: str, description: str = Body(...)):
    return AIJobGenerator(openai).generate_job_from_description(description)


@router.post("/description-from-job")
def generate_description_from_job(
    company_id: str, job: UserCreateJob, tone: PreferredTone = Body(...)
):
    return AIJobGenerator(openai).generate_description_from_job_details(job, tone)


@router.post("/improve-description")
def generate_improved_job_description(
    company_id: str, description: str = Body(...), tone: PreferredTone = Body(...)
):
    return AIJobGenerator(openai).generate_improved_job_description_from_draft(
        description, tone
    )
