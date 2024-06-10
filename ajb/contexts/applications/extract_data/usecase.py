from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.resumes.models import Resume
from ajb.vendor.pdf_plumber import extract_pdf_text_by_url, extract_docx_text_by_url
from ajb.vendor.openai.repository import AsyncOpenAIRepository
from ajb.contexts.applications.extract_data.ai_extractor import (
    AIResumeExtractor,
    ExtractedResume,
)


class EmptyResumeException(Exception):
    pass


class BadFileTypeException(Exception):
    pass


class ResumeExtractorUseCase(BaseUseCase):
    def __init__(self, request_scope: RequestScope, openai: AsyncOpenAIRepository):
        self.openai = openai
        super().__init__(request_scope)

    def extract_resume_text_and_url(self, resume_id: str) -> tuple[str, str]:
        resume: Resume = self.get_object(
            Collection.RESUMES,
            resume_id,
            self.request_scope,
            self.request_scope.user_id,
        )
        # Check file type and call method accordingly
        if not resume.file_type:
            raise BadFileTypeException

        text = ""
        try:
            text = extract_pdf_text_by_url(resume.resume_url)
        except Exception:
            pass

        if not text:
            try:
                text = extract_docx_text_by_url(resume.resume_url)
            except Exception:
                pass

        if not text:
            raise BadFileTypeException
        return text, resume.resume_url

    async def extract_resume_information(self, resume_text: str) -> ExtractedResume:
        if resume_text == "":
            raise EmptyResumeException
        return await AIResumeExtractor(
            self.openai
        ).get_candidate_profile_from_resume_text(
            resume_text
        )  # type: ignore
