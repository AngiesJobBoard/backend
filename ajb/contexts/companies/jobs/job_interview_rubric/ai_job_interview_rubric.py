from ajb.vendor.openai.repository import OpenAIRepository


class AIJobInterviewRubricMakerClass:
    def __init__(self, openai: OpenAIRepository | None = None) -> None:
        self.openai = openai or OpenAIRepository()

    def make_prompt(self): ...

    def get_job_data(self): ...

    def generate_rubric(self): ...
