from base64 import b64decode

from ajb.base import BaseUseCase, RepoFilterParams, Collection
from ajb.contexts.applications.events import IngressEvent

from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    RawIngressApplicationRepository,
)
from ajb.vendor.arango.models import Filter, Operator
from transformers.router import route_transformer_request
from migrations.base import MIGRATION_REQUEST_SCOPE


"""Pull all raw ingress that have no application ID and pass them to the transformer router"""


class ReRunApplicationUngressMigration(BaseUseCase):
    def get_all_raw_ingress_without_applications(self):
        return RawIngressApplicationRepository(self.request_scope).query(
            repo_filters=RepoFilterParams(
                filters=[
                    Filter(
                        field="application_id", operator=Operator.IS_NULL, value=None
                    )
                ]
            )
        )

    def run(self):
        all_raw_ingress, _ = self.get_all_raw_ingress_without_applications()
        for raw_ingress in all_raw_ingress:
            route_transformer_request(
                self.request_scope,
                IngressEvent(
                    company_id=raw_ingress.company_id,
                    ingress_id=raw_ingress.ingress_id,
                    raw_ingress_data_id=raw_ingress.id,
                ),
            )

    def download_pcm_ingress_file(self, raw_ingress_record_id: str, file_type: str):
        raw_record = self.get_object(
            Collection.RAW_INGRESS_APPLICATIONS, raw_ingress_record_id
        )
        resume_encoded = raw_record.data["resume_bytes"][0]
        resume_bytes = b64decode(resume_encoded)

        with open(f"downloaded_file.{file_type}", "wb") as file:
            file.write(resume_bytes)


def main():
    ReRunApplicationUngressMigration(MIGRATION_REQUEST_SCOPE).run()
