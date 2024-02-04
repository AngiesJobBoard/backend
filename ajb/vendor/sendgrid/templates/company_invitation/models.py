from ..base_email_data import BaseEmailData


class CompanyInvitation(BaseEmailData):
    companyName: str
    invitationLink: str
