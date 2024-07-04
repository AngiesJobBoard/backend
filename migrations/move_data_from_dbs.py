"""
This is a migration file that helps to copy the state from one db to another, whether remote to remote or remote local etc.
"""

import os
import time
from arango.client import ArangoClient
from pydantic import BaseModel

from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.vendor.arango.repository import StandardDatabase, ArangoDBRepository
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.models import (
    RawIngressApplication,
)
from migrations.base import MIGRATION_REQUEST_SCOPE


class MoveDataFromDbs(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        from_db: StandardDatabase,
        to_db: StandardDatabase,
    ):
        self.request_scope = request_scope
        self.from_db = from_db
        self.to_db = to_db

    def _update_raw_ingress_batch(self, batch: list[RawIngressApplication]) -> list:
        # Special case for raw_ingress_batch, we need to drop the raw resume bytes it is stored unnecessarily
        for idx, record in enumerate(batch):
            if record.data.get("resume_bytes"):
                batch[idx].data["resume_bytes"] = ""
        return batch

    def prepare_batch(self, batch: list[BaseModel]) -> list[dict]:
        batch_as_dict = [item.model_dump(mode="json") for item in batch]
        updated_keys = []
        for item in batch_as_dict:
            item["_key"] = item.pop("id")
            updated_keys.append(item)
        return updated_keys

    def migrate_collection(self, collection: Collection, truncate: bool, dry_run: bool):
        # Pull all values from the from_db collection, force write into to_db collection
        from_repo_scope = RequestScope(
            user_id=self.request_scope.user_id, db=self.from_db, kafka=None
        )
        from_repo = self.get_repository(collection, request_scope=from_repo_scope)
        all_items = []
        page = 0
        page_size = 250
        res = from_repo.get_all(page=page, page_size=page_size)
        all_items.extend(res)
        print(f"Found {len(all_items)} items in {collection.value}")
        while len(res) > 0:
            time.sleep(1)
            page += 1
            res = from_repo.get_all(page=page, page_size=page_size)
            all_items.extend(res)
            print(f"Found {len(all_items)} items in {collection.value}")

        to_collection = ArangoDBRepository(self.to_db, collection).db[collection.value]
        if truncate:
            # If request, delete and start over
            to_collection.truncate()

        BATCH_SIZE = 20
        for i in range(0, len(all_items), BATCH_SIZE):
            batch = all_items[i : i + BATCH_SIZE]
            if collection == Collection.RAW_INGRESS_APPLICATIONS:
                batch = self._update_raw_ingress_batch(batch)
            if not dry_run:
                to_collection.insert_many(self.prepare_batch(batch), overwrite=True)

    def run(self, truncate: bool = False, dry_run: bool = True):
        for collection in Collection:
            if (
                collection == Collection.COMPANY_SUBSCRIPTIONS
                or collection == Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING
            ):
                continue
            self.migrate_collection(collection, truncate, dry_run)


if __name__ == "__main__":
    from_db = ArangoClient(os.environ["FROM_DB_URL"]).db(
        name=os.environ["FROM_DB_NAME"],
        username=os.environ["FROM_DB_USERNAME"],
        password=os.environ["FROM_DB_PASSWORD"],
    )
    to_db = ArangoClient(os.environ["TO_DB_URL"]).db(
        name=os.environ["TO_DB_NAME"],
        username=os.environ["TO_DB_USERNAME"],
        password=os.environ["TO_DB_PASSWORD"],
    )
    MoveDataFromDbs(MIGRATION_REQUEST_SCOPE, from_db, to_db).run(
        truncate=True, dry_run=False
    )
