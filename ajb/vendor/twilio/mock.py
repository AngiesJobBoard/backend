class MockResponse:
    def __init__(self, *args, **kwargs):
        # Left blank intentionally
        pass

    sid = "test"


class MockMessages:
    def __init__(self, *args, **kwargs):
        self.sent_messages = {}

    def create(self, body: str, from_: str, to: str):
        self.sent_messages[to] = body
        return MockResponse(from_)


class MockTwilio:
    messages = MockMessages()

    def __init__(self, *args, **kwargs):
        # Left blank intentionally
        pass
