from ajb.base import BaseUseCase, Collection
from ajb.contexts.resumes.models import Resume
from ajb.vendor.pdf_plumber import extract_pdf_text_by_url

from .ai_extractor import AIResumeExtractor, ExtractedResume


class ResumeExtractorUseCase(BaseUseCase):
    def extract_resume_text(self, resume_id: str) -> str:
        resume: Resume = self.get_object(
            Collection.RESUMES,
            resume_id,
            self.request_scope,
            self.request_scope.user_id,
        )
        return extract_pdf_text_by_url(resume.resume_url)

    def extract_resume_information(self, resume_text: str) -> ExtractedResume:
        return AIResumeExtractor().get_candidate_profile_from_resume_text(resume_text)
