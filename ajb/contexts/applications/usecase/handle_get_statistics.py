from ajb.base import BaseUseCase
from ajb.base.schema import Collection
from ajb.contexts.applications.models import CompanyApplicationStatistics
from ajb.vendor.arango.repository import ArangoDBRepository


def get_filter_string(job_id: str | None = None):
    filter_string = "FILTER doc.company_id == @_BIND_VAR_0\n"
    if job_id:
        filter_string += " AND doc.job_id == @_BIND_VAR_1\n"
    return filter_string


def format_status_summary_query(job_id: str | None = None):
    query_string = f"""
    LET statusCounts = (
        FOR doc IN applications
        {get_filter_string(job_id)}
        COLLECT application_status = doc.application_status WITH COUNT INTO statusCount
    """
    query_string += "RETURN {application_status, statusCount}\n)"
    return query_string


def format_match_score_summary_query(job_id: str | None = None):
    query_string = f"""
    LET scoreBuckets = (
        FOR doc IN applications
        {get_filter_string(job_id)}
        LET scoreRange = (
            doc.application_match_score <= 30 ? '0-30' :
            doc.application_match_score > 30 && doc.application_match_score <= 70 ? '30-70' :
            doc.application_match_score > 70 ? '70+' :
            'Unknown' // Optional
        )
        COLLECT range = scoreRange WITH COUNT INTO rangeCount
    """
    query_string += "RETURN {range, rangeCount}\n)"
    return query_string


class ApplicationStatisticsResolver(BaseUseCase):

    def get_application_statistics(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> CompanyApplicationStatistics:
        status_query = format_status_summary_query(job_id)
        match_score_query = format_match_score_summary_query(job_id)

        full_query_string = ""
        full_query_string += status_query
        full_query_string += match_score_query
        full_query_string += "\nRETURN {statusCounts, scoreBuckets}"
        bind_vars = {"_BIND_VAR_0": company_id}
        if job_id:
            bind_vars["_BIND_VAR_1"] = job_id

        repo = ArangoDBRepository(self.request_scope.db, Collection.APPLICATIONS)
        res = repo.execute_custom_statement(full_query_string, bind_vars)
        return CompanyApplicationStatistics.from_arango_query(res)
