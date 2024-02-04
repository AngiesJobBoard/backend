import typing as t
from datetime import datetime
from arango.cursor import Cursor
from ajb.base import (
    Collection,
    ParentRepository,
    RepositoryRegistry,
    QueryFilterParams,
)
from ajb.base.events import SourceServices
from ajb.exceptions import EntityNotFound
from ajb.vendor.arango.models import Join, Filter, Operator
from ajb.utils import generate_random_short_code
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.applications.enumerations import USER_UPDATE

from .models import (
    UserCreatedApplication,
    Application,
    CreateRecruiterNote,
    RecruiterNote,
    CompanyApplicationView,
    UserApplicationView,
    ApplicationStatusRecord,
)
from .enumerations import ApplicationStatus


NOT_FOUND_TEXT = "Application not found"


class ApplicationRepository(ParentRepository[UserCreatedApplication, Application]):
    collection = Collection.APPLICATIONS
    entity_model = Application


class CompanyApplicationRepository(ApplicationRepository):
    def _company_get_application(self, company_id: str, application_id: str):
        original_application = self.get(application_id)
        if original_application.company_id != company_id:
            raise EntityNotFound(NOT_FOUND_TEXT)
        return original_application

    def company_updates_application_shortlist(
        self, company_id: str, application_id: str, new_shortlist_status: bool
    ):
        assert self._company_get_application(company_id, application_id)
        response = self.update_fields(
            application_id, application_is_shortlisted=new_shortlist_status
        )
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_shortlists_application(application_id)
        return response

    def create_recruiter_note(
        self, company_id: str, application_id: str, note: CreateRecruiterNote
    ) -> Application:
        original_application = self._company_get_application(company_id, application_id)
        new_note = RecruiterNote(**note.model_dump(), id=generate_random_short_code())
        original_application.recruiter_notes[new_note.id] = new_note
        return self.update_fields(
            application_id,
            recruiter_notes=original_application.model_dump(mode="json")[
                "recruiter_notes"
            ],
        )

    def update_recruiter_note(
        self,
        company_id: str,
        application_id: str,
        note_id: str,
        updated_note: CreateRecruiterNote,
    ) -> Application:
        original_application = self._company_get_application(company_id, application_id)
        note = original_application.recruiter_notes.get(note_id)
        if not note:
            raise EntityNotFound("Note not found")
        note.note = updated_note.note
        note.updated = datetime.utcnow()
        original_application.recruiter_notes[note_id] = note
        return self.update_fields(
            application_id,
            recruiter_notes=original_application.model_dump(mode="json")[
                "recruiter_notes"
            ],
        )

    def delete_recruiter_note(
        self, company_id: str, application_id: str, note_id: str
    ) -> bool:
        original_application = self._company_get_application(company_id, application_id)
        if not original_application.recruiter_notes.get(note_id):
            raise EntityNotFound("Note not found")
        del original_application.recruiter_notes[note_id]
        self.update_fields(
            application_id,
            recruiter_notes=original_application.model_dump(mode="json")[
                "recruiter_notes"
            ],
        )
        return True

    def update_application_status(
        self, company_id: str, application_id: str, new_status: ApplicationStatusRecord
    ) -> Application:
        original_application = self._company_get_application(company_id, application_id)
        original_application.application_status_history.append(new_status)
        response = self.update_fields(
            application_id,
            application_status_history=original_application.model_dump(mode="json")[
                "application_status_history"
            ],
        )

        if new_status.status == ApplicationStatus.REJECTED_BY_COMPANY:
            CompanyEventProducer(
                self.request_scope, SourceServices.API
            ).company_rejects_application(application_id)

        return response

    def get_company_view_list(
        self,
        company_id: str,
        query: QueryFilterParams = QueryFilterParams(),
        shortlist_only: bool = False,
    ):
        repo_filters = query.convert_to_repo_filters()
        repo_filters.filters.append(Filter(field="company_id", value=company_id))
        if shortlist_only:
            repo_filters.filters.append(
                Filter(
                    field="application_is_shortlisted",
                    value=True,
                )
            )
        results, count = self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="user",
                    to_collection="users",
                    from_collection_join_attr="user_id",
                ),
                Join(
                    to_collection_alias="resume",
                    to_collection="resumes",
                    from_collection_join_attr="resume_id",
                ),
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=CompanyApplicationView,
        )
        casted_results = t.cast(list[CompanyApplicationView], results)
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_views_applications(
            [result.id for result in casted_results],
            query.page,
        )
        return results, count

    def get_company_view_single(self, company_id: str, application_id: str):
        result = self.get_with_joins(
            id=application_id,
            joins=[
                Join(
                    to_collection_alias="user",
                    to_collection="users",
                    from_collection_join_attr="user_id",
                ),
                Join(
                    to_collection_alias="resume",
                    to_collection="resumes",
                    from_collection_join_attr="resume_id",
                ),
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            return_model=CompanyApplicationView,
        )
        casted_result = t.cast(CompanyApplicationView, result)
        if casted_result.company_id != company_id:
            raise EntityNotFound(NOT_FOUND_TEXT)
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_clicks_on_application(casted_result.id)
        self.update_fields(application_id, has_been_viewed_by_recruiters=True)
        return result

    def get_application_count(
        self,
        company_id: str,
        new_only: bool = False,
        start_date_filter: datetime | None = None,
        end_date_filter: datetime | None = None,
    ) -> int:
        bind_vars = {"company_id": company_id}
        query_text = f"FOR doc in {self.collection.value}"
        query_text += " FILTER doc.company_id == @company_id"
        if new_only:
            query_text += " FILTER LENGTH(ATTRIBUTES(doc.viewed_by_recruiters)) == 0"
        if start_date_filter:
            query_text += " FILTER doc.created_at >= @start_date"
            bind_vars["start_date"] = start_date_filter.isoformat()
        if end_date_filter:
            query_text += " FILTER doc.created_at <= @end_date"
            bind_vars["end_date"] = end_date_filter.isoformat()
        query_text += " RETURN doc"
        cursor = t.cast(
            Cursor,
            self.db.aql.execute(
                query_text, bind_vars=bind_vars, count=True  # type: ignore
            ),
        )
        return cursor.count() or 0


class UserApplicationRepository(ApplicationRepository):
    def _user_get_application(self, user_id: str, application_id: str):
        original_application = self.get(application_id)
        if original_application.user_id != user_id:
            raise EntityNotFound(NOT_FOUND_TEXT)
        return original_application

    def candidate_updates_application(
        self, user_id: str, application_id: str, new_status: USER_UPDATE
    ):
        assert self._user_get_application(user_id, application_id)
        return self.update_fields(application_id, application_status=new_status)

    def get_candidate_view_list(
        self,
        user_id: str | None = None,
        application_id: str | None = None,
        job_id: str | None = None,
        job_title: str | None = None,
        company_name: str | None = None,
        application_status: ApplicationStatus | None = None,
        query: QueryFilterParams = QueryFilterParams(),
    ):
        repo_filters = query.convert_to_repo_filters()
        if user_id:
            repo_filters.filters.append(Filter(field="user_id", value=user_id))
        if application_id:
            repo_filters.filters.append(Filter(field="_key", value=application_id))
        if job_id:
            repo_filters.filters.append(
                Filter(field="_key", value=job_id, collection_alias="job")
            )
        if job_title:
            repo_filters.filters.append(
                Filter(
                    field="position_title",
                    operator=Operator.CONTAINS,
                    value=job_title,
                    collection_alias="job",
                )
            )
        if company_name:
            repo_filters.filters.append(
                Filter(
                    field="name",
                    operator=Operator.CONTAINS,
                    value=company_name,
                    collection_alias="company",
                )
            )
        if application_status:
            repo_filters.filters.append(
                Filter(field="application_status", value=application_status)
            )
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="company",
                    to_collection="companies",
                    from_collection_join_attr="company_id",
                ),
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
                Join(
                    to_collection_alias="resume",
                    to_collection="resumes",
                    from_collection_join_attr="resume_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=UserApplicationView,
        )

    def get_candidate_view_single(self, user_id: str, application_id: str):
        result = self.get_with_joins(
            id=application_id,
            joins=[
                Join(
                    to_collection_alias="company",
                    to_collection="companies",
                    from_collection_join_attr="company_id",
                ),
                Join(
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
                Join(
                    to_collection_alias="resume",
                    to_collection="resumes",
                    from_collection_join_attr="resume_id",
                ),
            ],
            return_model=UserApplicationView,
        )
        casted_result = t.cast(UserApplicationView, result)  # type: ignore
        if casted_result.user_id != user_id:
            raise EntityNotFound(NOT_FOUND_TEXT)
        return result


RepositoryRegistry.register(ApplicationRepository)
