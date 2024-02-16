from ajb.base import (
    ParentRepository,
    Collection,
    RepositoryRegistry,
)

from .models import Resume, CreateResume


class ResumeRepository(ParentRepository[CreateResume, Resume]):
    collection = Collection.RESUMES
    entity_model = Resume


RepositoryRegistry.register(ResumeRepository)
