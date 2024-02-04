from ajb.base import (
    MultipleChildrenRepository,
    RequestScope,
    Collection,
    RepositoryRegistry,
)
from .models import JobTemplate, CreateJobTemplate


class JobTemplateRepository(MultipleChildrenRepository[CreateJobTemplate, JobTemplate]):
    collection = Collection.JOB_TEMPLATES
    entity_model = JobTemplate

    def __init__(self, request_scope: RequestScope, company_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )


RepositoryRegistry.register(JobTemplateRepository)
