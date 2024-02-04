from fastapi import APIRouter, Request, Depends, UploadFile, File

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.users.resumes.models import (
    UserCreateResume,
    Resume,
    ResumePaginatedResponse,
)
from ajb.contexts.users.resumes.repository import ResumeRepository
from ajb.contexts.users.resumes.usecase import ResumeUseCase
from ajb.contexts.users.resumes.extract_data.usecase import ResumeExtractorUseCase
from ajb.contexts.users.resumes.extract_data.ai_extractor import ExtractedResume
from ajb.contexts.users.resumes.suggestions.usecase import ResumeSuggestorUseCase

from api.vendors import storage

router = APIRouter(tags=["User Resumes"], prefix="/resumes")


@router.get("/", response_model=ResumePaginatedResponse)
def get_all_resumes(request: Request, query: QueryFilterParams = Depends()):
    """Gets the resumes for the current user"""
    results = ResumeRepository(request.state.request_scope).query(query)
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, ResumePaginatedResponse
    )


@router.get("/{resume_id}", response_model=Resume)
def get_resume_by_id(resume_id: str, request: Request):
    """Gets a resume by id for the current user"""
    return ResumeRepository(request.state.request_scope).get(resume_id)


@router.post("/", response_model=Resume)
def create_resume(request: Request, file: UploadFile = File(...)):
    """Creates a resume for the current user"""
    return ResumeUseCase(request.state.request_scope, storage).create_user_resume(
        request.state.request_scope.user_id,
        UserCreateResume(
            file_type=file.content_type or "application/pdf",
            file_name=file.filename or "resume.pdf",
            resume_data=file.file.read(),
        ),
    )


@router.put("/{resume_id}", response_model=Resume)
def update_resume(request: Request, resume_id: str, file: UploadFile = File(...)):
    """Updates a resume for the current user"""
    return ResumeUseCase(request.state.request_scope).update_user_resume(
        request.state.request_scope.user_id,
        resume_id,
        UserCreateResume(
            file_type=file.content_type or "application/pdf",
            file_name=file.filename or "resume.pdf",
            resume_data=file.file.read(),
        ),
    )


@router.delete("/{resume_id}")
def delete_resume(resume_id: str, request: Request):
    """Deletes a resume by id for the current user"""
    return ResumeUseCase(request.state.request_scope).delete_user_resume(
        request.state.request_scope.user_id, resume_id
    )


@router.get("/{resume_id}/extract", response_model=ExtractedResume)
def extract_resume_data(request: Request, resume_id: str):
    return ResumeExtractorUseCase(
        request.state.request_scope
    ).extract_resume_information(resume_id)


@router.get("/{resume_id}/suggest")
def suggested_resume_improvements(request: Request, resume_id: str):
    return ResumeSuggestorUseCase(request.state.request_scope).create_resume_suggestion(
        resume_id
    )
