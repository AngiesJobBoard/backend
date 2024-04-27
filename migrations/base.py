from ajb.base import RequestScope
from ajb.vendor.arango.repository import get_arango_db
from ajb.vendor.kafka.repository import KafkaProducerFactory


MIGRATION_REQUEST_SCOPE = RequestScope(
    user_id="migration",
    db=get_arango_db(),
    kafka=KafkaProducerFactory.get_client(),
)
