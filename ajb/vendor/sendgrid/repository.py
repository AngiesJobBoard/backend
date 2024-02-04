from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ajb.config.settings import SETTINGS
from ajb.vendor.jinja import Jinja2TemplateEngine

from .templates.base_email_data import BaseEmailData
from .client_factory import SendgridFactory


class SendgridRepository:
    def __init__(self, client: SendGridAPIClient | None = None):
        self.client = client or SendgridFactory.get_client()

    def send_email(self, to_emails: str, subject: str, html_content: str):
        data_as_mail = Mail(
            from_email=SETTINGS.SENDGRID_FROM_EMAIL,
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
        )
        return self.client.send(data_as_mail)

    def format_email_template(self, template_name: str, template_data: BaseEmailData):
        return Jinja2TemplateEngine().render_template(
            template_name, **template_data.to_str_dict()
        )

    def send_rendered_email_template(
        self,
        to_emails: str,
        subject: str,
        template_name: str,
        template_data: BaseEmailData,
    ):
        rendered_template = self.format_email_template(template_name, template_data)
        return self.send_email(to_emails, subject, rendered_template)
