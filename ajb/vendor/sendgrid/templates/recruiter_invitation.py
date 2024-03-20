from .base_email_data import BaseEmailData, SendgridTemplateId


class RecruiterInvitationData(BaseEmailData):
    companyName: str
    invitationLink: str
    templateId: SendgridTemplateId = SendgridTemplateId.RECRUITER_INVITATION
