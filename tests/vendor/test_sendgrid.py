from ajb.vendor.sendgrid.repository import SendgridRepository, SendgridFactory
from ajb.vendor.sendgrid.templates.example.models import ExampleModel


def test_send_email():
    client = SendgridFactory._return_mock()
    repo = SendgridRepository(client)  # type: ignore

    repo.send_email(
        to_emails="test@email.com",
        subject="test subject",
        html_content="test content",
    )

    assert len(client.sent_emails) == 1


def test_format_email_template():
    repo = SendgridRepository()
    rendered_email = repo.format_email_template(
        "example", ExampleModel(firstName="steve")
    )
    assert rendered_email == "<h1>Hello steve!</h1>"
