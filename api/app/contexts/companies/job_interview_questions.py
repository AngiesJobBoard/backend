"""
These endpoints are for potential questions for the recruiter to ask the candidate.
Additonal endpoints are for getting and setting the questions for a specific application.
"""

from fastapi import APIRouter, Request

from ajb.contexts.applications.interview.interview_questions.models import (
    CreateInterviewQuestions,
    InterviewQuestions,
)
from ajb.contexts.applications.interview.interview_questions.repository import (
    InterviewQuestionsRepository,
)
from ajb.contexts.applications.interview.interview_questions.usecase import (
    InterviewQuestionsUseCase,
)
from api.middleware import scope
from api.vendors import openai

router = APIRouter(
    tags=["Job Interview Questions"],
    prefix="/companies/{company_id}/jobs/{job_id}/applications/{application_id}",
)


@router.get("/", response_model=InterviewQuestions)
def get_job_interview_questions(request: Request, application_id: str):
    """
    Get the job interview questions for a specific application.
    """
    return InterviewQuestionsRepository(scope(request), application_id).get_sub_entity()


@router.post("/", response_model=InterviewQuestions)
def set_job_interview_questions(
    request: Request, application_id: str, questions: CreateInterviewQuestions
):
    """
    Create a job interview questions for a specific application.
    """
    return InterviewQuestionsRepository(scope(request), application_id).set_sub_entity(
        questions
    )


@router.post("/generate", response_model=InterviewQuestions)
def generate_job_interview_questions(request: Request, application_id: str):
    """
    Generate a job interview questions for a specific application.
    """
    return InterviewQuestionsUseCase(
        scope(request), openai
    ).generate_interview_questions(application_id)
