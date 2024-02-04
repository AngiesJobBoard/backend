from ajb.base import ParentRepository, RepositoryRegistry, Collection

from .models import CreateUser, User


class UserRepository(ParentRepository[CreateUser, User]):
    collection = Collection.USERS
    entity_model = User

    def get_user_by_email(self, email: str):
        return self.get_one(email=email)


RepositoryRegistry.register(UserRepository)
