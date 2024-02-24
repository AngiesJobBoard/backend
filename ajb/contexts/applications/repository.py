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
from ajb.vendor.arango.models import Join, Filter
from ajb.utils import generate_random_short_code
from ajb.contexts.companies.events import CompanyEventProducer

from .models import (
    CreateApplication,
    Application,
    CreateRecruiterNote,
    RecruiterNote,
    CompanyApplicationView,
    ApplicationStatusRecord,
)
from .enumerations import ApplicationStatus


NOT_FOUND_TEXT = "Application not found"


class ApplicationRepository(ParentRepository[CreateApplication, Application]):
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
                    to_collection_alias="job",
                    to_collection="jobs",
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=repo_filters,
            return_model=CompanyApplicationView,
        )
        casted_results = t.cast(list[CompanyApplicationView], results)
        return results, count

    def get_company_view_single(self, company_id: str, application_id: str):
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
        return casted_result

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

    def create_applications_from_csv(
        self, company_id: str, job_id: str, raw_candidates: list[dict]
    ):
        candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        created_applications = self.create_many(candidates)

        # Create a company event for each application created to perform the match
        event_producter = CompanyEventProducer(self.request_scope, SourceServices.API)
        for application in created_applications:
            event_producter.company_calculates_match_score(application)
        return created_applications


RepositoryRegistry.register(ApplicationRepository)
