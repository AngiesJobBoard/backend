from datetime import datetime
from ajb.base import Collection, RepoFilterParams, Pagination, BaseUseCase
from ajb.contexts.companies.recruiters.models import Recruiter
from ajb.vendor.arango.models import Join, Filter, Operator

from .models import (
    CreateApplicationUpdate,
    CompanyApplicationUpdateView,
    UpdateType,
)


class RecruiterUpdatesUseCase(BaseUseCase):
    def add_recruiter_comment(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        recruiter_user_id: str,
        comment: str,
        added_by_ajb_admin: bool = False,
    ):
        recruiter_update_repo = self.get_repository(
            Collection.APPLICATION_RECRUITER_UPDATES, self.request_scope, application_id
        )
        recruiter_repo = self.get_repository(Collection.COMPANY_RECRUITERS)
        recruiter: Recruiter = recruiter_repo.get_one(
            company_id=company_id,
            user_id=recruiter_user_id,
        )
        current_application_status = self.get_object(
            Collection.APPLICATIONS, application_id
        ).application_status
        return recruiter_update_repo.create(
            CreateApplicationUpdate(
                comment=comment,
                new_application_status=current_application_status,
                added_by_ajb_admin=added_by_ajb_admin,
                type=UpdateType.NOTE,
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
                recruiter_id=recruiter.id,
                recruiter_user_id=recruiter_user_id,
            )
        )

    def update_application_status(
        self,
        company_id: str,
        job_id: str,
        application_id: str,
        recruiter_user_id: str,
        new_application_status: str,
        comment: str | None = None,
    ):
        recruiter_update_repo = self.get_repository(
            Collection.APPLICATION_RECRUITER_UPDATES, self.request_scope, application_id
        )
        recruiter_repo = self.get_repository(Collection.COMPANY_RECRUITERS)
        recruiter: Recruiter = recruiter_repo.get_one(
            company_id=company_id,
            user_id=recruiter_user_id,
        )
        return recruiter_update_repo.create(
            CreateApplicationUpdate(
                comment=comment,
                new_application_status=new_application_status,
                added_by_ajb_admin=False,
                type=UpdateType.STATUS_CHANGE,
                company_id=company_id,
                job_id=job_id,
                application_id=application_id,
                recruiter_id=recruiter.id,
                recruiter_user_id=recruiter_user_id,
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
        recruiter_update_repo = self.get_repository(
            Collection.APPLICATION_RECRUITER_UPDATES, self.request_scope, application_id
        )
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

        return recruiter_update_repo.query_with_joins(
            joins=[
                Join(
                    to_collection=Collection.USERS.value,
                    to_collection_alias="recruiter_user",
                    from_collection_join_attr="recruiter_user_id",
                )
            ],
            repo_filters=query,
            return_model=CompanyApplicationUpdateView,
        )
