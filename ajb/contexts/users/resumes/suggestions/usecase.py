from ajb.base import BaseUseCase, Collection
from ajb.vendor.pdf_plumber import extract_pdf_text_by_url
from ajb.contexts.users.resumes.models import Resume

from .ai_suggestor import AIResumeSuggestor


class ResumeSuggestorUseCase(BaseUseCase):
    def create_resume_suggestion(self, resume_id: str) -> str:
        resume_repo = self.get_repository(
            Collection.RESUMES, self.request_scope, self.request_scope.user_id
        )
        resume: Resume = resume_repo.get(resume_id)
        resume_text = extract_pdf_text_by_url(resume.resume_url)
        return AIResumeSuggestor(resume_text).provide_suggestion()
