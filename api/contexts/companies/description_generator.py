from fastapi import APIRouter, Request,  Body

from ajb.contexts.companies.job_generator.ai_generator import AIJobGenerator
from ajb.contexts.companies.jobs.models import UserCreateJob
from ajb.common.models import PreferredTone

from api.vendors import openai, mixpanel


router = APIRouter(
    tags=["AI Company Job Generator"], prefix="/companies/{company_id}/job-generator"
)


@router.post("/job-from-description", response_model=UserCreateJob)
def generate_job_from_description(request: Request, company_id: str, description: str = Body(...)):
    results = AIJobGenerator(openai).generate_job_from_description(description)
    mixpanel.job_description_is_generated(request.state.request_scope.user_id, company_id, "job_from_description")
    return results


@router.post("/description-from-job")
def generate_description_from_job(
    request: Request, company_id: str, job: UserCreateJob, tone: PreferredTone = Body(...)
):
    results = AIJobGenerator(openai).generate_description_from_job_details(job, tone)
    mixpanel.job_description_is_generated(request.state.request_scope.user_id, company_id, "description_from_job")
    return results


@router.post("/improve-description")
def generate_improved_job_description(
    request: Request, company_id: str, description: str = Body(...), tone: PreferredTone = Body(...)
):
    results = AIJobGenerator(openai).generate_improved_job_description_from_draft(
        description, tone
    )
    mixpanel.job_description_is_generated(request.state.request_scope.user_id, company_id, "improved_description")
    return results
