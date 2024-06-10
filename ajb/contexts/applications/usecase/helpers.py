from ajb.base.schema import Collection
from ajb.common.models import ApplicationQuestion
from ajb.contexts.companies.jobs.models import Job


class ApplicationHelpersUseCase:
    def __init__(self, main):
        self.main = main

    def _get_job_questions(self, job_id: str) -> list[ApplicationQuestion]:
        job: Job = self.main.get_object(Collection.JOBS, job_id)
        if not job.application_questions_as_strings:
            return []
        return [
            ApplicationQuestion(question=question)
            for question in job.application_questions_as_strings
        ]

    def _get_filter_string(self, job_id: str | None = None):
        filter_string = "FILTER doc.company_id == @_BIND_VAR_0\n"
        if job_id:
            filter_string += " AND doc.job_id == @_BIND_VAR_1\n"
        return filter_string

    def _format_status_summary_query(self, job_id: str | None = None):
        query_string = f"""
        LET statusCounts = (
            FOR doc IN applications
            {self._get_filter_string(job_id)}
            COLLECT application_status = doc.application_status WITH COUNT INTO statusCount
        """
        query_string += "RETURN {application_status, statusCount}\n)"
        return query_string

    def _format_match_score_summary_query(self, job_id: str | None = None):
        query_string = f"""
        LET scoreBuckets = (
            FOR doc IN applications
            {self._get_filter_string(job_id)}
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
