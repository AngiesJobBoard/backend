from ajb.vendor.arango.repository import get_arango_db
from ajb.vendor.kafka.client_factory import KafkaProducerFactory
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.vendor.openai.repository import OpenAIRepository


print("Initializing vendor dependencies")

db = get_arango_db()
kafka_producer = KafkaProducerFactory.get_client()
storage = FirebaseStorageRepository()
openai = OpenAIRepository()
