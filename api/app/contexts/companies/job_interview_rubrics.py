"""
These endpoints are for recruiters to create a scoring rubric for their job interviews.
Additional endpoints are for candidates to view the rubric and submit their scores.
"""

from fastapi import APIRouter, Request

from ajb.contexts.companies.jobs.job_interview_rubric.models import (
    CreateJobInterviewRubric,
    JobInterviewRubric,
)
from ajb.contexts.companies.jobs.job_interview_rubric.repository import (
    JobInterviewRubricRepository,
)
from ajb.contexts.companies.jobs.job_interview_rubric.usecase import (
    JobInterviewRubricUseCase,
)
from api.middleware import scope
from api.vendors import openai

router = APIRouter(
    tags=["Job Interview Rubrics"], prefix="/companies/{company_id}/jobs/{job_id}"
)


@router.get("/", response_model=JobInterviewRubric)
def get_job_interview_rubric(request: Request, job_id: str):
    """
    Get the job interview rubric for a specific job.
    """
    return JobInterviewRubricRepository(scope(request), job_id).get_sub_entity()


@router.post("/", response_model=JobInterviewRubric)
def set_job_interview_rubric(
    request: Request, job_id: str, rubric: CreateJobInterviewRubric
):
    """
    Create a job interview rubric for a specific job.
    """
    return JobInterviewRubricRepository(scope(request), job_id).set_sub_entity(rubric)


@router.post("/generate", response_model=JobInterviewRubric)
def generate_job_interview_rubric(request: Request, job_id: str):
    """
    Generate a job interview rubric for a specific job.
    """
    return JobInterviewRubricUseCase(
        scope(request), openai
    ).generate_job_interview_rubric(job_id)
