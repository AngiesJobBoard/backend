from ajb.vendor.openai.repository import OpenAIRepository


class AIResumeSuggestor:
    def __init__(self, resume_text: str):
        self.repo = OpenAIRepository()
        self.resume_text = resume_text

    def provide_suggestion(self) -> str:
        prompt = f"Given the following resume text, provide a suggestion on how to improve it.\n\n{self.resume_text}"
        results = self.repo.text_prompt(prompt, max_tokens=1000)
        return results
