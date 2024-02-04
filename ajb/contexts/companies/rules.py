from ajb.base import BaseRepository
from ajb.base.rules import EntityDoesNotExistRule, RuleSet
from ajb.vendor.arango.models import Filter


class CompanySlugNotTakenRule(EntityDoesNotExistRule):
    code = "company_with_slug_exists"
    message = "Company with slug already exists"

    def __init__(self, repository: BaseRepository, company_slug: str):
        super().__init__(
            repository=repository,
            filters=[Filter(field="slug", value=company_slug)],
        )


class CompanyCreationRuleSet(RuleSet):
    def __init__(
        self,
        repository: BaseRepository,
        company_slug: str | None,
    ):
        self.repository = repository
        self.company_slug = company_slug

    def _get_rules(self):
        if self.company_slug:
            yield CompanySlugNotTakenRule(self.repository, self.company_slug)
