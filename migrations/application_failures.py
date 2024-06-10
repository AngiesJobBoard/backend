"""
This will rerun the async action for any failed applications to attempt to process them again
"""

import aiohttp
import asyncio

from ajb.base import BaseUseCase, Collection
from ajb.base.events import BaseKafkaMessage, KafkaTopic, ApplicationEvent
from ajb.contexts.applications.models import Application, ScanStatus
from ajb.contexts.applications.events import ApplicantAndCompany
from ajb.vendor.openai.repository import AsyncOpenAIRepository, OpenAIRepository
from services.resolvers.applications import ApplicationEventsResolver
from migrations.base import MIGRATION_REQUEST_SCOPE


class ApplicationFailureReRunUseCase(BaseUseCase):
    openai = OpenAIRepository()

    def get_failed_resume_scans(self) -> list[Application]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        return application_repo.get_all(resume_scan_status=ScanStatus.FAILED.value)

    def get_failed_application_match(self) -> list[Application]:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        failed = application_repo.get_all(match_score_status=ScanStatus.FAILED.value)
        started = application_repo.get_all(match_score_status=ScanStatus.STARTED.value)
        pending = application_repo.get_all(match_score_status=ScanStatus.PENDING.value)
        return failed + started + pending

    async def rerun_failed_resume_scan(self):
        failed_scans = self.get_failed_resume_scans()
        print(f"Found {len(failed_scans)} failed resume scans")

        # AJBTODO finish this migration bit

    async def rerun_failed_application_match(self):
        failed_application_matches = self.get_failed_application_match()
        print(f"Found {len(failed_application_matches)} failed application matches")

        for application in failed_application_matches:
            print(
                f"Trying to resubmit application for {application.id} - {application.name}"
            )
            try:
                await ApplicationEventsResolver(
                    message=BaseKafkaMessage(
                        requesting_user_id="migration",
                        data=ApplicantAndCompany(
                            company_id=application.company_id,
                            job_id=application.job_id,
                            application_id=application.id,
                        ).model_dump(),
                        topic=KafkaTopic.APPLICATIONS,
                        event_type=ApplicationEvent.GET_MATCH_SCORE,
                        source_service="migration",
                    ),
                    request_scope=MIGRATION_REQUEST_SCOPE,
                    openai=self.openai,
                ).company_gets_match_score()
                print(
                    f"Successfully resubmitted application for {application.id} - {application.name}!!\n"
                )
            except Exception as e:
                print(
                    f"Failed to resubmit application for {application.id} - {application.name}: {e}\n"
                )
                continue


def main():
    usecase = ApplicationFailureReRunUseCase(MIGRATION_REQUEST_SCOPE)
    asyncio.run(usecase.rerun_failed_application_match())
