from ..base_email_data import BaseEmailData


class CompanyRejectsUser(BaseEmailData):
    candidate_name: str
    position: str
    company_name: str
    supportEmail: str = "support@angiesjobboard.com"
