from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.job_templates.models import (
    CreateJobTemplate,
    JobTemplate,
    PaginatedJobTemplate,
    UserCreateJob,
    UserCreateTemplate,
)
from ajb.contexts.companies.job_templates.repository import JobTemplateRepository


router = APIRouter(
    tags=["Company Job Templates"], prefix="/companies/{company_id}/job-templates"
)


@router.get("/", response_model=PaginatedJobTemplate)
def get_all_job_templates(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all job templates for a company"""
    response = JobTemplateRepository(request.state.request_scope, company_id).query(
        query
    )
    return build_pagination_response(
        response, query.page, query.page_size, request.url._url, PaginatedJobTemplate
    )


@router.get("/autocomplete")
def get_job_template_autocomplete(
    request: Request, company_id: str, prefix: str, field: str = "template_name"
):
    """Gets a list of job templates that match the prefix"""
    return JobTemplateRepository(
        request.state.request_scope, company_id
    ).get_autocomplete(field, prefix)


@router.post("/", response_model=UserCreateTemplate)
def create_job_template(request: Request, company_id: str, job: UserCreateJob):
    """Creates a job template for a company"""
    return JobTemplateRepository(request.state.request_scope, company_id).create(
        CreateJobTemplate(**job.model_dump(), company_id=company_id)
    )


@router.get("/{template_id}", response_model=JobTemplate)
def get_job_template(request: Request, company_id: str, template_id: str):
    """Gets a job template for a company"""
    return JobTemplateRepository(request.state.request_scope, company_id).get(
        template_id
    )


@router.patch("/{template_id}", response_model=JobTemplate)
def update_job_template(
    request: Request, company_id: str, template_id: str, job: UserCreateJob
):
    """Updates a job template for a company"""
    return JobTemplateRepository(request.state.request_scope, company_id).update(
        template_id, job
    )


@router.delete("/{template_id}")
def delete_job_template(request: Request, company_id: str, template_id: str):
    """Deletes a job template for a company"""
    return JobTemplateRepository(request.state.request_scope, company_id).delete(
        template_id
    )
