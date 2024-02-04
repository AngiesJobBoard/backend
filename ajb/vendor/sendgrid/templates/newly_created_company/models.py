from ..base_email_data import BaseEmailData


class NewlyCreatedCompany(BaseEmailData):
    companyName: str
    supportEmail: str
