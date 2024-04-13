from ajb.base import BaseUseCase, Collection
from ajb.contexts.applications.models import Application

from migrations.base import MIGRATION_REQUEST_SCOPE


class UpdateApplicationModel(BaseUseCase):
    """
    We previously had status as a mandatory field with a default value, now we want them to be null unless
    the value is set by the recruiter
    """

    def get_all_applications(self) -> list[Application]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        return application_repo.get_all()

    def update_application_status(self, application: Application):
        application_repo = self.get_repository(Collection.APPLICATIONS)
        updated_application: Application = application_repo.update_fields(
            application.id, application_status=None
        )
        print(f"Application: {application.id}")
        print(f"Original Status: {application.application_status}")
        print(f"Updated Status: {updated_application.application_status}")

    def run(self):
        applications = self.get_all_applications()
        for application in applications:
            self.update_application_status(application)


def main():
    UpdateApplicationModel(MIGRATION_REQUEST_SCOPE).run()
