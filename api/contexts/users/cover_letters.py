from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.users.cover_letters.models import (
    CreateCoverLetter,
    CoverLetter,
    CoverLetterPaginatedResponse,
)
from ajb.contexts.users.cover_letters.repository import CoverLetterRepository

router = APIRouter(tags=["User Cover Letters"], prefix="/cover-letters")


@router.get("/", response_model=CoverLetterPaginatedResponse)
def get_all_cover_letters(request: Request, query: QueryFilterParams = Depends()):
    """Gets the cover letters for the current user"""
    results = CoverLetterRepository(request.state.request_scope).query(query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        CoverLetterPaginatedResponse,
    )


@router.get("/{id}", response_model=CoverLetter)
def get_cover_letter_by_id(id: str, request: Request):
    """Gets a cover letter by id for the current user"""
    return CoverLetterRepository(request.state.request_scope).get(id)


@router.post("/", response_model=CoverLetter)
def create_cover_letter(request: Request, cover_letter: CreateCoverLetter):
    """Creates a cover letter for the current user"""
    return CoverLetterRepository(request.state.request_scope).create(cover_letter)


@router.put("/{id}", response_model=CoverLetter)
def update_cover_letter(id: str, request: Request, cover_letter: CreateCoverLetter):
    """Updates a cover letter for the current user"""
    return CoverLetterRepository(request.state.request_scope).update(id, cover_letter)


@router.delete("/{id}")
def delete_cover_letter(id: str, request: Request):
    """Deletes a cover letter by id for the current user"""
    return CoverLetterRepository(request.state.request_scope).delete(id)
