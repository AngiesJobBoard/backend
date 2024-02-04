from ..base_email_data import BaseEmailData


class NewUserWelcomeData(BaseEmailData):
    firstName: str
    supportEmail: str = "support@angiesjobboard.com"
