from ajb.base import (
    Collection,
    ParentRepository,
    RepositoryRegistry,
)

from .models import Company, CreateCompany


class CompanyRepository(ParentRepository[CreateCompany, Company]):
    collection = Collection.COMPANIES
    entity_model = Company


RepositoryRegistry.register(CompanyRepository)
