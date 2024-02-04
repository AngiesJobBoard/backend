from ajb.vendor.arango.repository import get_arango_db
from ajb.vendor.algolia.repository import (
    AlgoliaSearchRepository,
    AlgoliaInsightsRepository,
    AlgoliaIndex,
)
from ajb.vendor.kafka.client_factory import KafkaProducerFactory
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.vendor.openai.repository import OpenAIRepository


print("Initializing vendor dependencies")

db = get_arango_db()
kafka_producer = KafkaProducerFactory.get_client()
search_jobs = AlgoliaSearchRepository(AlgoliaIndex.JOBS)
job_insights = AlgoliaInsightsRepository(AlgoliaIndex.JOBS)
search_companies = AlgoliaSearchRepository(AlgoliaIndex.COMPANIES)
company_insights = AlgoliaInsightsRepository(AlgoliaIndex.COMPANIES)
search_candidates = AlgoliaSearchRepository(AlgoliaIndex.CANDIDATES)
candidate_insights = AlgoliaInsightsRepository(AlgoliaIndex.CANDIDATES)
storage = FirebaseStorageRepository()
openai = OpenAIRepository()
