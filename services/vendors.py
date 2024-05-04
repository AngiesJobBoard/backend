from ajb.base import RequestScope
from ajb.vendor.arango.repository import get_arango_db
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.kafka.client_factory import KafkaProducerFactory
from ajb.base.events import BaseKafkaMessage


print("Initializing vendor dependencies")

db = get_arango_db()
openai = OpenAIRepository()
sendgrid = SendgridRepository()

print("Vendor dependencies initialized")


def make_request_scope(message: BaseKafkaMessage):
    return RequestScope(
        user_id=message.requesting_user_id,
        db=db,
        kafka=KafkaProducerFactory.get_client(),
    )
