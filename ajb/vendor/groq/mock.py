from groq import Groq
from groq.types.chat import ChatCompletion
from groq.types.chat.chat_completion_message import ChatCompletionMessage


class MockCompletions:
    def __init__(self, return_content):
        self.return_content = return_content

    # pylint: disable=unused-argument
    def create(self, *args, **kwargs):
        return ChatCompletion(
            id="test",
            choices=[
                {
                    "finish_reason": "stop",
                    "index": 1,
                    "message": ChatCompletionMessage(
                        content=self.return_content,
                        role="assistant",
                        tool_calls=None,
                    ),
                    "logprobs": None,
                }
            ],
            created=0,
            model="",
            object="chat.completion",
        )


class MockChat:
    def __init__(self, return_content):
        self.completions = MockCompletions(return_content)


class MockGroq(Groq):
    # pylint: disable=super-init-not-called
    def __init__(self, return_content=None):
        self.chat = MockChat(return_content)  # type: ignore
        self.base_url = ""
