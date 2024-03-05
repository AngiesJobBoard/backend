from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.resumes.models import Resume
from ajb.vendor.pdf_plumber import extract_pdf_text_by_url
from ajb.vendor.openai.repository import AsyncOpenAIRepository

from .ai_extractor import AIResumeExtractor, ExtractedResume


class ResumeExtractorUseCase(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, openai: AsyncOpenAIRepository
    ):
        self.openai = openai
        super().__init__(request_scope)

    def extract_resume_text_and_url(self, resume_id: str) -> tuple[str, str]:
        resume: Resume = self.get_object(
            Collection.RESUMES,
            resume_id,
            self.request_scope,
            self.request_scope.user_id,
        )
        return extract_pdf_text_by_url(resume.resume_url), resume.resume_url

    async def extract_resume_information(self, resume_text: str) -> ExtractedResume:
        return await AIResumeExtractor(self.openai).get_candidate_profile_from_resume_text(
            resume_text
        )
