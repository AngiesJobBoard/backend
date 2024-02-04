from ajb.base import RequestScope
from ajb.vendor.arango.repository import get_arango_db
from ajb.vendor.algolia.repository import (
    AlgoliaSearchRepository,
    AlgoliaInsightsRepository,
    AlgoliaIndex,
)
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.base.events import BaseKafkaMessage

db = get_arango_db()
search_jobs = AlgoliaSearchRepository(AlgoliaIndex.JOBS)
job_insights = AlgoliaInsightsRepository(AlgoliaIndex.JOBS)
search_companies = AlgoliaSearchRepository(AlgoliaIndex.COMPANIES)
company_insights = AlgoliaInsightsRepository(AlgoliaIndex.COMPANIES)
search_candidates = AlgoliaSearchRepository(AlgoliaIndex.CANDIDATES)
candidate_insights = AlgoliaInsightsRepository(AlgoliaIndex.CANDIDATES)
openai = OpenAIRepository()
sendgrid = SendgridRepository()


def make_request_scope(message: BaseKafkaMessage):
    return RequestScope(user_id=message.requesting_user_id, db=db, company_id=None)
