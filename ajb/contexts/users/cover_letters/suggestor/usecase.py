from ajb.base import BaseUseCase, Collection
from ajb.common.models import PreferredTone

from .ai_suggestor import AICoverLetterGenerator


class CoverLetterSuggestorUsecase(BaseUseCase):
    def generate_cover_letter_from_draft(
        self,
        draft: str,
        job_id: str,
        tone: PreferredTone,
    ) -> str:
        job = self.get_object(Collection.JOBS, job_id)
        return AICoverLetterGenerator().generate_cover_letter_from_draft(
            draft=draft,
            job=job,
            tone=tone,
        )
