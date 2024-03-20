from concurrent.futures import ThreadPoolExecutor
from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.common.models import QuestionStatus
from ajb.contexts.applications.models import Application, UpdateApplication
from ajb.vendor.openai.repository import AsyncOpenAIRepository

from .ai_question_answers import AIApplicantionQuestionAnswer


class ApplicantQuestionsUsecase(BaseUseCase):
    def __init__(self, request_scope: RequestScope, openai: AsyncOpenAIRepository):
        self.request_scope = request_scope
        self.openai = openai

    async def update_application_with_questions_answered(
        self, application_id: str
    ) -> None:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        application: Application = application_repo.get(application_id)
        if not application.application_questions or not application.qualifications:
            return None

        stored_exception = None
        question_answerer = AIApplicantionQuestionAnswer(self.openai)
        for idx, question in enumerate(application.application_questions):
            if question.question_status == QuestionStatus.PENDING_ANSWER:
                try:
                    updated_application_question = (
                        await question_answerer.answer_question(
                            question.question, application.qualifications
                        )
                    )
                    application.application_questions[idx] = (
                        updated_application_question
                    )
                except Exception as e:
                    stored_exception = e
                    application.application_questions[idx].question_status = (
                        QuestionStatus.FAILED
                    )
                    application.application_questions[idx].error_text = str(e)

        application_repo.update(
            application.id,
            UpdateApplication(application_questions=application.application_questions),
        )
        if stored_exception:
            raise stored_exception

    def update_many_application_questions(self, application_id_list: list[str]):
        with ThreadPoolExecutor(max_workers=5) as executor:
            for application_id in application_id_list:
                executor.submit(
                    self.update_application_with_questions_answered, application_id
                )
        return True
