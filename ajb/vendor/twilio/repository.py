from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from ajb.config.settings import SETTINGS

from .client_factory import TwilioFactory


class TwilioRepository:
    def __init__(self, client: Client | None = None):
        self.client = client or TwilioFactory.get_client()

    def send_message(self, to_number: str, message: str):
        try:
            response = self.client.messages.create(
                body=message, from_=SETTINGS.TWILIO_PHONE_NUMBER, to=to_number
            )
            return response.sid
        except TwilioRestException as e:
            return f"An error occurred: {str(e)}"

    def format_message_from_template(self, template_name: str, **kwargs):
        with open(f"ajb/vendor/twilio/templates/{template_name}.txt") as f:
            template = f.read()
        return template.format(**kwargs)
