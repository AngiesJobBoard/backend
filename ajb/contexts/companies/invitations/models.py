from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base import BaseDataModel, PaginatedResponse, BaseDeepLinkData

from ..models import RecruiterRole


class UserCreateInvitation(BaseModel):
    email_address: str
    role: RecruiterRole


class CreateInvitation(UserCreateInvitation):
    inviting_user_id: str
    company_id: str


class Invitation(BaseDataModel, CreateInvitation):
    ...


@dataclass
class InvitationPaginatedResponse(PaginatedResponse[Invitation]):
    data: list[Invitation]


class InvitationData(BaseDeepLinkData):
    email_address: str
    invitation_id: str
    company_id: str
