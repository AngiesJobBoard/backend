from ..base_email_data import BaseEmailData


class JobApplicationData(BaseEmailData):
    position: str
    company: str
    name: str
    email: str
    phone: str | None
    resumeLink: str
