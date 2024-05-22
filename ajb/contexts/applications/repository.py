import typing as t
from ajb.base import (
    Collection,
    ParentRepository,
    RepositoryRegistry,
    QueryFilterParams,
    RepoFilterParams,
    Pagination,
)
from ajb.exceptions import EntityNotFound
from ajb.vendor.arango.models import Filter, Operator, Join
from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume

from .models import (
    CompanyApplicationView,
    CreateApplication,
    Application,
    AdminApplicationView,
    ApplicantAndJob,
    ScanStatus,
    UpdateApplication,
    Qualifications,
    WorkHistory,
    Location,
)


class ApplicationRepository(ParentRepository[CreateApplication, Application]):
    collection = Collection.APPLICATIONS
    entity_model = Application

    def update_application_with_parsed_information(
        self,
        *,
        application_id: str,
        resume_url: str | None,
        raw_resume_text: str,
        resume_information: ExtractedResume,
    ) -> Application:
        original_application = self.get(application_id)
        return self.update(
            application_id,
            UpdateApplication(
                name=(
                    original_application.name if original_application.name is not None else
                    f"{resume_information.first_name} {resume_information.last_name}".title()
                ),
                email=original_application.email if original_application.email is not None else resume_information.email,
                phone=original_application.phone if original_application.phone is not None else resume_information.phone_number,
                extracted_resume_text=raw_resume_text,
                resume_url=resume_url,
                qualifications=Qualifications(
                    most_recent_job=(
                        WorkHistory(
                            job_title=resume_information.most_recent_job_title,
                            company_name=resume_information.most_recent_job_company,
                        )
                        if resume_information.most_recent_job_title
                        and resume_information.most_recent_job_company
                        else None
                    ),
                    work_history=resume_information.work_experience or [],
                    education=resume_information.education or [],
                    skills=resume_information.skills or [],
                    licenses=resume_information.licenses or [],
                    certifications=resume_information.certifications or [],
                    language_proficiencies=resume_information.languages or [],
                ),
                user_location=original_application.user_location or (
                    Location(
                        city=resume_information.city, state=resume_information.state
                    )
                    if resume_information.city and resume_information.state
                    else None
                ),
            ),
        )


class CompanyApplicationRepository(ApplicationRepository):
    def _company_get_application(self, company_id: str, application_id: str):
        original_application = self.get(application_id)
        if original_application.company_id != company_id:
            raise EntityNotFound("Application not found")
        return original_application

    def get_company_view_list(
        self,
        company_id: str,
        query: QueryFilterParams | RepoFilterParams | None = None,
        job_id: str | None = None,
        match_score: int | None = None,
        new_only: bool = False,
        resume_text_contains: str | None = None,
        has_required_skill: str | None = None,
        status_filter: list[str] | None = None,
    ):
        if isinstance(query, QueryFilterParams):
            repo_filters = query.convert_to_repo_filters()
        else:
            repo_filters = query or RepoFilterParams()
        if company_id:
            repo_filters.filters.append(Filter(field="company_id", value=company_id))
        if job_id:
            repo_filters.filters.append(Filter(field="job_id", value=job_id))
        if match_score:
            repo_filters.filters.append(
                Filter(
                    field="application_match_score",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=match_score,
                )
            )
        if new_only:
            repo_filters.filters.append(
                Filter(
                    field="application_status",
                    operator=Operator.IS_NULL,
                    value=None,
                )
            )
            repo_filters.filters.append(
                Filter(
                    field="active",
                    value=True,
                    collection_alias="job",
                )
            )
        if resume_text_contains:
            repo_filters.filters.append(
                Filter(
                    field="extracted_resume_text",
                    operator=Operator.CONTAINS,
                    value=resume_text_contains,
                )
            )
        if has_required_skill:
            repo_filters.filters.append(
                Filter(
                    field="qualifications.skills",
                    operator=Operator.IN,
                    value=has_required_skill,
                )
            )
        if status_filter:
            for status in status_filter:
                repo_filters.filters.append(
                    Filter(
                        field="application_status", value=status, and_or_operator="OR"
                    )
                )
            # If any status filters (otherwise all apps are returned) include a filter for jobs that are active only
            repo_filters.filters.append(
                Filter(
                    field="active",
                    value=True,
                    collection_alias="job",
                )
            )
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=CompanyApplicationView,
        )

    def get_all_pending_applications(
        self,
        company_id: str,
        query: QueryFilterParams | RepoFilterParams | None = None,
        job_id: str | None = None,
        include_failed: bool = False,
    ):
        if isinstance(query, QueryFilterParams):
            repo_filters = query.convert_to_repo_filters()
        else:
            repo_filters = query or RepoFilterParams()

        repo_filters.filters.extend(
            [
                Filter(
                    field="resume_scan_status",
                    value=ScanStatus.PENDING.value,
                    and_or_operator="OR",
                ),
                Filter(
                    field="resume_scan_status",
                    value=ScanStatus.STARTED.value,
                    and_or_operator="OR",
                ),
                Filter(
                    field="match_score_status",
                    value=ScanStatus.STARTED.value,
                    and_or_operator="OR",
                ),
            ]
        )
        if include_failed:
            repo_filters.filters.append(
                Filter(
                    field="resume_scan_status",
                    value=ScanStatus.FAILED.value,
                    and_or_operator="OR",
                )
            )
        return self.get_company_view_list(company_id, repo_filters, job_id=job_id)

    def get_all_company_applications_from_email(
        self, company_id: str, email: str
    ) -> list[ApplicantAndJob]:
        repo_query = RepoFilterParams(
            pagination=Pagination(page=0, page_size=50),
            filters=[
                Filter(field="company_id", value=company_id),
                Filter(field="email", value=email),
            ],
        )
        res, _ = self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=repo_query,
            return_model=ApplicantAndJob,
        )
        casted_result = t.cast(list[ApplicantAndJob], res)
        return casted_result

    def get_company_view_single(self, application_id: str):
        result = self.get_with_joins(
            id=application_id,
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            return_model=CompanyApplicationView,
        )
        casted_result = t.cast(CompanyApplicationView, result)
        if casted_result.email:
            other_applications = self.get_all_company_applications_from_email(
                casted_result.company_id, casted_result.email
            )
        else:
            other_applications = []
        return CompanyApplicationView(
            **casted_result.model_dump(exclude={"other_applications"}),
            other_applications=other_applications,
        )

    def get_admin_application_view(
        self,
        repo_filters: QueryFilterParams | RepoFilterParams | None = None,
    ):
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
                Join(
                    to_collection_alias="company",
                    to_collection="companies",
                    from_collection_join_attr="company_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=AdminApplicationView,
        )


RepositoryRegistry.register(ApplicationRepository)
