from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.contexts.users.models import AlgoliaCandidateSearch, User


class CreateSavedCandidate(BaseModel):
    user_id: str
    saved_for_job_id: str | None = None
    saved_for_application_id: str | None = None


class SavedCandidate(CreateSavedCandidate, BaseDataModel): ...


class SavedCandidatesListObject(SavedCandidate):
    candidate: User | AlgoliaCandidateSearch


@dataclass
class SavedCandidatesPaginatedResponse(PaginatedResponse[SavedCandidatesListObject]):
    data: list[SavedCandidatesListObject]
