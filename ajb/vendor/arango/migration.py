from ajb.config.settings import SETTINGS
from ajb.base import (
    Collection,
    View,
    VIEW_DEFINITIONS,
    RequestScope,
)
from ajb.base.schema import COLLECTION_INDEXES
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.admin.users.repository import AdminUserRepository, CreateAdminUser
from ajb.contexts.admin.users.models import AdminRoles
from ajb.contexts.users.usecase import UserUseCase
from ajb.contexts.static.repository import StaticDataRepository
from ajb.utils import generate_random_short_code
from ajb.vendor.clerk.models import SimpleClerkCreateUser
from ajb.exceptions import EntityNotFound

from .client_factory import ArangoClientFactory
from .constants import Constants


class ArangoMigrator:
    def __init__(
        self,
        db_name: str = SETTINGS.ARANGO_DB_NAME,
    ):
        self.client = ArangoClientFactory.get_client()
        self.collections = Collection
        self.views = View
        self.view_definitions = VIEW_DEFINITIONS
        self.db_name = db_name

        # Create provided db if not exists
        system_db = self.client.db(
            Constants.SYSTEM_DB_NAME,
            username=SETTINGS.ARANGO_USERNAME,
            password=SETTINGS.ARANGO_PASSWORD,
        )
        if not system_db.has_database(self.db_name):
            system_db.create_database(self.db_name)
        self.db = self.client.db(
            self.db_name,
            username=SETTINGS.ARANGO_USERNAME,
            password=SETTINGS.ARANGO_PASSWORD,
        )
        self.request_scope = RequestScope(user_id="SYSTEM", db=self.db, company_id=None)

    def create_collections(self):
        for collection in self.collections:
            if self.db.has_collection(collection.value):
                continue
            self.db.create_collection(collection.value)
            print(f"Created collection {collection.value}")

    def create_views(self):
        current_views = [view["name"] for view in self.db.views()]  # type: ignore
        for view in self.views:
            if view.value in current_views:
                continue

            if view not in self.view_definitions:
                print(f"View {view.value} does not have a definition")
                continue
            self.db.create_arangosearch_view(
                name=view.value, properties=self.view_definitions[view].model_dump()
            )
            print(f"Created view {view.value}")

    def create_system_user(self):
        # Check if system user exists
        try:
            UserRepository(self.request_scope).get_user_by_email(
                email=SETTINGS.SYSTEM_USER_EMAIL
            )
            print("System user already exists")
            return
        except EntityNotFound:
            # System user doesn't exist, create it
            pass

        created_user = UserUseCase(self.request_scope).admin_create_user(
            SimpleClerkCreateUser(
                first_name="System",
                last_name="Admin",
                email_address=SETTINGS.SYSTEM_USER_EMAIL,
                password=generate_random_short_code(16),
                skip_password_checks=True,
                skip_password_requirement=True,
            ),
            force_if_exists=True,
        )
        AdminUserRepository(self.request_scope).create(
            CreateAdminUser(
                user_id=created_user.id,
                email=SETTINGS.SYSTEM_USER_EMAIL,
                role=AdminRoles.SUPER_ADMIN,
            ),
            overridden_id=created_user.id,
        )

    def load_default_static_data(self):
        StaticDataRepository(self.request_scope).load_default_data()

    def delete_collections_that_dont_exist_in_collections(self):
        for collection in self.db.collections():  # type: ignore
            if collection["name"] not in [c.value for c in self.collections]:
                if collection.get("system", False):
                    continue
                self.db.delete_collection(collection["name"])
                print(f"Deleted collection {collection}")

    def create_collection_indexes(self):
        for collection, indexes_to_create in COLLECTION_INDEXES.items():
            res = self.db.collection(collection.value).add_hash_index(
                fields=[",".join(indexes_to_create)],
                unique=False,
                name=f"{collection.value}_index",
                in_background=True,
                deduplicate=False
            )
            print(f"Index established:", res)

    def execute(self):
        self.create_collections()
        self.create_views()
        self.create_collection_indexes()
        print("\nDatabase setup complete\n")
        self.create_system_user()
        self.load_default_static_data()
        self.delete_collections_that_dont_exist_in_collections()

    def run_migrations(self):
        self.collections = Collection
        self.views = View
        self.view_definitions = VIEW_DEFINITIONS
        self.execute()
