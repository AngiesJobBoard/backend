from ajb.base import Collection, MultipleChildrenRepository, RepositoryRegistry

from .models import CreateInvitation, Invitation


class InvitationRepository(MultipleChildrenRepository[CreateInvitation, Invitation]):
    collection = Collection.RECRUITER_INVITATIONS
    entity_model = Invitation

    def __init__(self, request_scope, company_id: str):
        super().__init__(request_scope, Collection.COMPANIES, company_id)
        self.company_id = company_id

    def get_all_invitations_for_company(self) -> tuple[list[Invitation], int]:
        return self.query(company_id=self.company_id)


RepositoryRegistry.register(InvitationRepository)
