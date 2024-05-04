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
    WEBHOOKS = SETTINGS.KAFKA_WEBHOOKS_TOPIC

    @classmethod
    def get_all_topics(cls):
        return [topic.value for topic in cls.__members__.values()]


class CompanyEvent(str, Enum):
    """Represents a business action that can be taken on a company"""

    COMPANY_IS_CREATED = "company_is_created"
    COMPANY_CREATES_JOB = "company_creates_job"
    COMPANY_UPDATES_JOB = "company_updates_job"
    COMPANY_DELETES_JOB = "company_deletes_job"


class ApplicationEvent(str, Enum):
    APPLICATION_IS_SUBMITTED = "application_is_submitted"
    APPLICATION_IS_UPDATED = "application_is_updated"
    APPLICATION_IS_DELETED = "application_is_deleted"
    UPLOAD_RESUME = "upload_resume"
    INGRESS_EVENT = "ingress_event"


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
    WEBHOOK = "webhook"  # Created based on a webhook request


class BaseEventProducer:
    def __init__(
        self,
        request_scope: RequestScope,
        source_service: SourceServices,
    ):
        self.request_scope = request_scope
        self.source_service = source_service
        self.producer = KafkaProducerRepository(request_scope.kafka)

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
