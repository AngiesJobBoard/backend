"""
This module will take an application and answer all pending questions
"""

from ajb.vendor.openai.repository import AsyncOpenAIRepository
from ajb.common.models import AnswerEnum, ApplicationQuestion, QuestionStatus
from ajb.contexts.applications.models import Qualifications
from ajb.utils import closest_string_enum_match


class AIApplicantionQuestionAnswer:
    def __init__(self, openai: AsyncOpenAIRepository):
        self.openai = openai

    async def answer_question(
        self, question: str, qualifications: Qualifications
    ) -> ApplicationQuestion:
        prompt = f"""
            You are an expert job recruiter and you are answering a question on behalf of a candidate given their qualifications.
            The question is: {question}.
            The candidate's qualifications are: {qualifications}.
            Provide a JSON response with the keys 'answer', 'confidence', and 'reasoning'.
            'answer' should be one of the following: {AnswerEnum}.
            'confidence' should be a number between 0 and 10.
            'reasoning' should be a string.
        """
        response = await self.openai.json_prompt(prompt, max_tokens=4000)
        return ApplicationQuestion(
            question=question,
            question_status=QuestionStatus.ANSWERED,
            answer=AnswerEnum(
                closest_string_enum_match(response["answer"], AnswerEnum)
            ),
            confidence=response["confidence"],
            reasoning=response["reasoning"],
        )
