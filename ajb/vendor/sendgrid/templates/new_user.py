from .base_email_data import BaseEmailData, SendgridTemplateId


class NewlyCreatedUser(BaseEmailData):
    userFirstName: str
    templateId: SendgridTemplateId = SendgridTemplateId.NEWLY_CREATED_USER
