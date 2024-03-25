from datetime import datetime
from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RequestScope,
    RepoFilterParams,
    Pagination,
)
from ajb.vendor.arango.models import Join, Filter, Operator
from ajb.contexts.applications.enumerations import ApplicationStatus

from .models import (
    CreateApplicationUpdate,
    ApplicationUpdate,
    CompanyApplicationUpdateView,
    UpdateType,
)


class RecruiterUpdatesRepository(
    MultipleChildrenRepository[CreateApplicationUpdate, ApplicationUpdate]
):
    collection = Collection.APPLICATION_RECRUITER_NOTES
    entity_model = ApplicationUpdate

    def __init__(self, request_scope: RequestScope, application_id: str | None = None):
        super().__init__(request_scope, Collection.APPLICATIONS, application_id)

    def add_recruiter_comment(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        recruiter_id: str,
        comment: str,
        added_by_ajb_admin: bool = False,
    ):
        return self.create(
            CreateApplicationUpdate(
                comment=comment,
                new_application_status=None,
                added_by_ajb_admin=added_by_ajb_admin,
                type=UpdateType.NOTE,
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
                recruiter_id=recruiter_id,
            )
        )

    def update_application_status(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        recruiter_id: str,
        new_application_status: ApplicationStatus,
        comment: str | None = None,
    ):
        return self.create(
            CreateApplicationUpdate(
                comment=comment,
                new_application_status=new_application_status,
                added_by_ajb_admin=False,
                type=UpdateType.STATUS_CHANGE,
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
                recruiter_id=recruiter_id,
            )
        )

    def add_to_shortlist(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        recruiter_id: str,
        comment: str | None = None,
    ):
        return self.create(
            CreateApplicationUpdate(
                comment=comment,
                new_application_status=None,
                added_by_ajb_admin=False,
                type=UpdateType.ADD_TO_SHORTLIST,
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
                recruiter_id=recruiter_id,
            )
        )

    def remove_from_shortlist(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        recruiter_id: str,
        comment: str | None = None,
    ):
        return self.create(
            CreateApplicationUpdate(
                comment=comment,
                new_application_status=None,
                added_by_ajb_admin=False,
                type=UpdateType.REMOVE_FROM_SHORTLIST,
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
                recruiter_id=recruiter_id,
            )
        )

    def get_application_update_timeline(
        self,
        company_id: str,
        job_id: str | None = None,
        application_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 0,
        page_size: int = 25,
    ):
        query = RepoFilterParams(
            pagination=Pagination(page=page, page_size=page_size),
            filters=[
                Filter(
                    field="company_id",
                    value=company_id,
                ),
            ],
        )
        if job_id:
            query.filters.append(Filter(field="job_id", value=job_id))
        if application_id:
            query.filters.append(Filter(field="application_id", value=application_id))
        if start_date:
            query.filters.append(
                Filter(
                    field="created_at",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=start_date,
                )
            )
        if end_date:
            query.filters.append(
                Filter(
                    field="created_at",
                    operator=Operator.LESS_THAN_EQUAL,
                    value=end_date,
                )
            )

        return self.query_with_joins(
            joins=[
                Join(
                    to_collection=Collection.USERS.value,
                    to_collection_alias="recruiter",
                    from_collection_join_attr="recruiter_id",
                )
            ],
            repo_filters=query,
            return_model=CompanyApplicationUpdateView,
        )
