from pydantic import BaseModel
from ajb.base.events import (
    BaseEventProducer,
    CreateKafkaMessage,
    KafkaTopic,
    UserEvent,
)

from .models import User


class UserAndJob(BaseModel):
    user_id: str
    company_id: str
    job_id: str
    user_is_anonymous: bool


class UserJobAndApplication(UserAndJob):
    application_id: str
    resume_id: str


class UserAndJobs(BaseModel):
    user_id: str
    companies_jobs_and_positions: list[tuple[str, str, int]]
    user_is_anonymous: bool


class UserAndCompany(BaseModel):
    user_id: str
    company_id: str
    user_is_anonymous: bool


class UserAndCompanies(BaseModel):
    user_id: str
    companies_and_positions: list[tuple[str, int]]
    user_is_anonymous: bool


class UserEventProducer(BaseEventProducer):
    def _user_event(self, data: dict, event: UserEvent):
        self.send(
            CreateKafkaMessage(
                requesting_user_id=self.request_scope.user_id,
                data=data,
            ),
            topic=KafkaTopic.USERS,
            event_type=event,
        )

    def user_created_event(self, created_user: User):
        self._user_event(
            data=created_user.model_dump(mode="json"),
            event=UserEvent.USER_IS_CREATED,
        )
