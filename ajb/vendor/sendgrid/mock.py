from sendgrid.helpers.mail import Mail


class MockSendgrid:
    def __init__(self, *args, **kwargs):
        self.sent_emails = []

    def send(self, mail: Mail):
        self.sent_emails.append(
            {
                "subject": mail.subject,
                "html_content": mail._contents,
            }
        )
