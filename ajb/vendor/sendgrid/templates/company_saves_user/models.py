from ..base_email_data import BaseEmailData


class CompanySavesUser(BaseEmailData):
    candidate_name: str
    supportEmail: str = "support@angiesjobboard.com"
