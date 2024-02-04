from ajb.vendor.twilio.repository import TwilioRepository, TwilioFactory


def test_send_message():
    client = TwilioFactory._return_mock()
    repo = TwilioRepository(client)  # type: ignore
    repo.send_message("1234567890", "Hello World!")

    assert client.messages.sent_messages["1234567890"] == "Hello World!"


def test_format_message_from_template():
    repo = TwilioRepository()
    name = "John"
    token = "123456"
    seconds = 60

    formatted_text = repo.format_message_from_template(
        "example", name=name, token=token, seconds=seconds
    )
    assert (
        formatted_text
        == f"Hello {name}, your example token is {token} and it will expire in {seconds} seconds. Thanks!"
    )
