from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ajb.config.settings import SETTINGS

from .templates.base_email_data import BaseEmailData
from .client_factory import SendgridFactory


class SendgridRepository:
    def __init__(self, client: SendGridAPIClient | None = None):
        self.client = client or SendgridFactory.get_client()

    def send_custom_email(self, to_emails: str, subject: str, html_content: str):
        mail = Mail(
            from_email=SETTINGS.SENDGRID_FROM_EMAIL,
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
        )
        return self.client.send(mail)

    def send_email_template(self, to_emails: str, subject: str, template_data: BaseEmailData):
        if template_data.templateId.value is None:
            raise ValueError("TemplateId is required")

        mail = Mail(
            from_email=SETTINGS.SENDGRID_FROM_EMAIL,
            to_emails=to_emails,
            subject=subject,
        )
        mail.template_id = template_data.templateId.value
        mail.dynamic_template_data = template_data.to_str_dict()
        r = self.client.send(mail)
        print(f"Email sent to {to_emails} with status code {r.status_code}")
        return r
