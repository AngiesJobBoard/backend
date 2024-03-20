from ajb.vendor.sendgrid.repository import SendgridRepository, SendgridFactory
from ajb.vendor.sendgrid.templates.base_email_data import (
    BaseEmailData,
    SendgridTemplateId,
)


def test_send_custom_email():
    client = SendgridFactory._return_mock()
    repo = SendgridRepository(client)  # type: ignore

    repo.send_custom_email(
        to_emails="test@email.com",
        subject="test subject",
        html_content="test content",
    )
    assert len(client.sent_emails) == 1


def test_send_email_template():
    client = SendgridFactory._return_mock()
    repo = SendgridRepository(client)  # type: ignore

    repo.send_email_template(
        to_emails="test@email.com",
        subject="test subject",
        template_data=BaseEmailData(templateId=SendgridTemplateId.RECRUITER_INVITATION),
    )
    assert len(client.sent_emails) == 1
