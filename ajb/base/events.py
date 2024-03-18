"""
This module is responsible for defining events that can be triggered by data operations.
These events can be used to trigger other operations, such as sending emails or creating
other data objects. All events are sent through Kafka topics
and can be consumed by one or multiple consumer groups.
"""

from typing import Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from ajb.base import RequestScope
from ajb.config.settings import SETTINGS
from ajb.vendor.kafka.repository import KafkaProducerRepository


class KafkaGroup(str, Enum):
    """A Group represents a set of consumers that will receive the same message"""

    DEFAULT = "default"


class KafkaTopic(str, Enum):
    """A topic represents a group of business actions"""

    COMPANIES = SETTINGS.KAFKA_COMPANIES_TOPIC
    APPLICATIONS = SETTINGS.KAFKA_APPLICATIONS_TOPIC
    USERS = SETTINGS.KAFKA_USERS_TOPIC

    @classmethod
    def get_all_topics(cls):
        return [topic.value for topic in cls.__members__.values()]


class CompanyEvent(str, Enum):
    """Represents a business action that can be taken on a company"""

    COMPANY_IS_CREATED = "company_is_created"
    COMPANY_VIEWS_APPLICATIONS = "company_views_applications"
    COMPANY_CLICKS_ON_APPLICATION = "company_clicks_on_application"
    COMPANY_SHORTLISTS_APPLICATION = "company_shortlists_application"
    COMPANY_REJECTS_APPLICATION = "company_rejects_application"


class ApplicationEvent(str, Enum):
    CALCULATE_MATCH_SCORE = "calculate_match_score"
    EXTRACT_APPLICATION_FILTERS = "extract_application_filters"
    ANSWER_JOB_FILTER_QUESTIONS = "answer_job_filter_questions"
    UPLOAD_RESUME = "upload_resume"


class UserEvent(str, Enum):
    """Represents a business action that can be taken on a user"""

    USER_IS_CREATED = "user_is_created"


class CreateKafkaMessage(BaseModel):
    """This is the data model created by a system to send to Kafka"""

    requesting_user_id: str
    data: dict[str, Any] = Field(default_factory=dict)


class BaseKafkaMessage(CreateKafkaMessage):
    """All data sent through Kafka will minimally contain this data"""

    topic: KafkaTopic
    message_time: datetime = datetime.now()

    event_type: str  #  Expected to be one of the event Enums below, each represents a business action
    source_service: str  # Marks where the message originated from (API, worker, etc.)


class SourceServices(str, Enum):
    """Represents the service that triggered the event"""

    API = "api"  # Created based on an API request
    SERVICES = "services"  # Created based on a service request
    ADMIN = "admin"  # Created based on an admin request


class BaseEventProducer:
    def __init__(
        self,
        request_scope: RequestScope,
        source_service: SourceServices,
    ):
        self.request_scope = request_scope
        self.source_service = source_service
        self.producer = KafkaProducerRepository(request_scope.kafka_producer)

    def send(
        self,
        message: CreateKafkaMessage,
        topic: KafkaTopic,
        event_type: Enum,
    ):
        message = BaseKafkaMessage(
            requesting_user_id=self.request_scope.user_id,
            data=message.data,
            topic=topic,
            event_type=event_type.value,
            source_service=self.source_service.value,
        )
        self.producer.publish(
            topic=topic.value, message=message.model_dump(mode="json")
        )
