from ajb.base import RequestScope
from ajb.contexts.applications.models import ScanStatus
from ajb.contexts.applications.repository import (
    ApplicationRepository,
    CreateApplication,
)


def create_example_applications(
    company_id: str, job_id_1: str, job_id_2: str, request_scope: RequestScope
):
    repo = ApplicationRepository(request_scope)
    repo.create(
        CreateApplication(
            company_id=company_id,
            job_id=job_id_1,
            name="Bobby Joe",
            email="joe@ajbtest.com",
            resume_scan_status=ScanStatus.COMPLETED,
            match_score_status=ScanStatus.COMPLETED,
        )
    )
    repo.create(
        CreateApplication(
            company_id=company_id,
            job_id=job_id_2,
            name="Sally Funkytown",
            email="sally@ajbtest.com",
            resume_scan_status=ScanStatus.COMPLETED,
            match_score_status=ScanStatus.COMPLETED,
        )
    )
