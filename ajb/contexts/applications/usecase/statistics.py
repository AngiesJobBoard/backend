from ajb.base.schema import Collection
from ajb.contexts.applications.models import CompanyApplicationStatistics
from ajb.vendor.arango.repository import ArangoDBRepository


class ApplicationStatisticsUseCase:
    def __init__(self, main):
        self.main = main

    def get_application_statistics(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> CompanyApplicationStatistics:
        status_query = self.main.helpers._format_status_summary_query(job_id)
        match_score_query = self.main.helpers._format_match_score_summary_query(job_id)

        full_query_string = ""
        full_query_string += status_query
        full_query_string += match_score_query
        full_query_string += "\nRETURN {statusCounts, scoreBuckets}"
        bind_vars = {"_BIND_VAR_0": company_id}
        if job_id:
            bind_vars["_BIND_VAR_1"] = job_id

        repo = ArangoDBRepository(self.main.request_scope.db, Collection.APPLICATIONS)
        res = repo.execute_custom_statement(full_query_string, bind_vars)
        return CompanyApplicationStatistics.from_arango_query(res)
