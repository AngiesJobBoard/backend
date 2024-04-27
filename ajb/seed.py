"""
This is a module that helps to seed a database with some data for testing purposes
"""

from ajb.base import RequestScope
from ajb.config.settings import SETTINGS
from ajb.vendor.arango.client_factory import ArangoClientFactory

# Import fixtures from testing and apply them to the database
from ajb.fixtures.applications import ApplicationFixture


class Seeder:
    def __init__(self):
        client = ArangoClientFactory.get_client()
        db = client.db(SETTINGS.ARANGO_DB_NAME)
        self.request_scope = RequestScope(user_id="db_seed", db=db, kafka=None)

    def seed_applications(self):
        ApplicationFixture(self.request_scope).create_all_application_data()


def seed_db():
    Seeder().seed_applications()


if __name__ == "__main__":
    seed_db()
