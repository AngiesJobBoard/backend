from ajb.base import BaseUseCase, Collection
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.models import RawIngressApplication
from ajb.config.settings import SETTINGS

from migrations.base import MIGRATION_REQUEST_SCOPE


class RawIngressJobsMigration(BaseUseCase):
    def update_raw_ingress(self, ingress_record: RawIngressApplication):
        if ingress_record.application_id is None:
            return
        application = self.get_object(Collection.APPLICATIONS, ingress_record.application_id)
        raw_ingress_repo = self.get_repository(Collection.RAW_INGRESS_APPLICATIONS)
        raw_ingress_repo.update_fields(
            ingress_record.id,
            job_id=application.job_id
        )
    
    def update_all_ingress_records(self):
        raw_ingress_repo = self.get_repository(Collection.RAW_INGRESS_APPLICATIONS)
        for record in raw_ingress_repo.get_all():
            try:
                self.update_raw_ingress(record)
            except Exception as e:
                print(f"Failed to update record {record.id}: {e}")
                continue



if __name__ == "__main__":
    use_case = RawIngressJobsMigration(MIGRATION_REQUEST_SCOPE)
    use_case.update_all_ingress_records()
