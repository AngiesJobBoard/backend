from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage


class MockCompletions:
    def __init__(self, return_content):
        self.return_content = return_content

    def create(self, *args, **kwargs):
        return ChatCompletion(
            id="test",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=1,
                    message=ChatCompletionMessage(
                        content=self.return_content, role="assistant"
                    ),
                    logprobs=None,
                )
            ],
            created=0,
            model="",
            object="chat.completion",
        )


class MockChat:
    def __init__(self, return_content):
        self.completions = MockCompletions(return_content)


class MockOpenAI(OpenAI):
    def __init__(self, return_content=None):
        self.chat = MockChat(return_content)  # type: ignore
        self.base_url = ""
