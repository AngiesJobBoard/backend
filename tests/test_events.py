from ajb.base.events import SourceServices, KafkaTopic
from ajb.contexts.users.events import UserEventProducer

from ajb.fixtures.users import UserFixture


def test_user_event_producer(request_scope):
    user_event_producer = UserEventProducer(request_scope, SourceServices.API)
    created_user = UserFixture(request_scope).create_user()
    user_event_producer.user_created_event(created_user)
    assert len(request_scope.kafka_producer.messages[KafkaTopic.USERS.value]) == 1
