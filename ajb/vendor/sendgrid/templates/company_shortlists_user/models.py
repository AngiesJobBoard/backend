from ..base_email_data import BaseEmailData


class CompanyShortlistsUser(BaseEmailData):
    position: str
    candidate_name: str
    company_name: str
    application_date: str
    supportEmail: str = "support@angiesjobboard.com"
