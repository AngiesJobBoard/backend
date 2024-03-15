from concurrent.futures import ThreadPoolExecutor
import pytest
from arango.database import StandardDatabase

from ajb.base import Collection, RequestScope
from ajb.config.settings import SETTINGS
from ajb.vendor.arango.client_factory import ArangoClientFactory
from ajb.vendor.arango.migration import ArangoMigrator
from ajb.vendor.arango.constants import Constants
from ajb.vendor.kafka.client_factory import KafkaProducerFactory


@pytest.fixture(scope="session", autouse=True)
def db():
    SETTINGS.LOCAL_TESTING = True
    client = ArangoClientFactory.get_client()
    system_db = client.db(Constants.SYSTEM_DB_NAME)
    test_db_name = "unit_test_db"
    if system_db.has_database(test_db_name):
        system_db.delete_database(test_db_name)
    system_db.create_database(test_db_name)
    migrator = ArangoMigrator(db_name=test_db_name)  # type: ignore
    migrator.run_migrations()
    db = migrator.client.db(test_db_name)
    yield db
    system_db.delete_database(test_db_name)


@pytest.fixture(scope="function", autouse=True)
def teardown_db(db: StandardDatabase):
    yield
    with ThreadPoolExecutor() as executor:
        for collection in Collection:
            executor.submit(db.collection(collection.value).truncate)


@pytest.fixture(scope="function")
def request_scope(db: StandardDatabase):
    yield RequestScope(
        user_id="test",
        db=db,
        kafka_producer=KafkaProducerFactory._return_mock(),
        company_id=None,
    )
    