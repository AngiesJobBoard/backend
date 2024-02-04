from fastapi import APIRouter, Body, Request

from ajb.contexts.users.cover_letters.suggestor.usecase import (
    CoverLetterSuggestorUsecase,
)
from ajb.common.models import PreferredTone


router = APIRouter(tags=["AI Cover Letter Helper"], prefix="/cover-letter-helper")


@router.post("/generate")
def generate_improved_cover_letter(
    request: Request,
    cover_letter: str = Body(...),
    job_id: str = Body(...),
    tone: PreferredTone = Body(...),
):
    return CoverLetterSuggestorUsecase(
        request.state.request_scope
    ).generate_cover_letter_from_draft(cover_letter, job_id, tone)
