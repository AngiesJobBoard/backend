from .base_email_data import BaseEmailData, SendgridTemplateId


class NewlyCreatedCompany(BaseEmailData):
    companyName: str
    templateId: SendgridTemplateId = SendgridTemplateId.NEWLY_CREATED_COMPANY
