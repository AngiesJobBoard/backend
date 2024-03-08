from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.resumes.models import Resume
from ajb.vendor.pdf_plumber import extract_pdf_text_by_url, extract_docx_text_by_url
from ajb.vendor.openai.repository import AsyncOpenAIRepository
from ajb.contexts.applications.extract_data.ai_extractor import AIResumeExtractor, ExtractedResume


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
        # Check file type and call method accordingly
        if not resume.file_type:
            raise ValueError("File type not provided")

        if "pdf" in resume.file_type:
            return extract_pdf_text_by_url(resume.resume_url), resume.resume_url
        
        if "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in resume.file_type:
            return extract_docx_text_by_url(resume.resume_url), resume.resume_url
        
        raise ValueError("File type not supported")

    async def extract_resume_information(self, resume_text: str) -> ExtractedResume:
        return await AIResumeExtractor(self.openai).get_candidate_profile_from_resume_text(
            resume_text
        )
