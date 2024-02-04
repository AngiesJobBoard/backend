from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.companies.jobs.models import (
    Job,
    UserCreateJob,
)
from ajb.contexts.admin.jobs.models import (
    CreateAdminJobPostApproval,
    JobApprovalStatus,
    AdminJobPostApproval,
)
from ajb.contexts.admin.jobs.usecase import (
    JobApprovalUseCase,
    AdminCreateApprovalUpdate,
)
from ajb.vendor.algolia.repository import AlgoliaSearchRepository, AlgoliaIndex
from ajb.exceptions import (
    FailedToPostJobException,
    EntityNotFound,
    MissingJobFieldsException,
    FailedToUpdateJobException,
)


class JobUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        aloglia_jobs: AlgoliaSearchRepository | None = None,
    ):
        self.request_scope = request_scope
        self.aloglia_jobs = aloglia_jobs or AlgoliaSearchRepository(AlgoliaIndex.JOBS)

    def submit_job_for_approval(
        self, company_id: str, job_id: str
    ) -> AdminJobPostApproval:
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job: Job = job_repo.get(job_id)
        try:
            job.check_for_missing_fields()
        except MissingJobFieldsException as exc:
            raise FailedToPostJobException(exc.message)

        admin_approval_repo = self.get_repository(Collection.ADMIN_JOB_APPROVALS)

        # Check if job has been submitted already
        try:
            submission: AdminJobPostApproval = admin_approval_repo.get_one(
                company_id=company_id, job_id=job_id
            )
        except EntityNotFound:
            # Create first submission
            submission = admin_approval_repo.create(
                CreateAdminJobPostApproval(
                    company_id=company_id,
                    job_id=job_id,
                    requesting_user=self.request_scope.user_id,
                )
            )

            # Update it with the initial status
            return JobApprovalUseCase(self.request_scope).update_job_approval_status(
                submission.id,
                user_id=self.request_scope.user_id,
                is_admin_update=False,
                updates=AdminCreateApprovalUpdate(
                    approval_status=JobApprovalStatus.PENDING,
                    reason="Initial Submission by user",
                ),
            )

        # Submission can not be in pending status
        if submission.current_approval_status == JobApprovalStatus.PENDING:
            raise FailedToPostJobException(f"Job {job_id} is already pending approval")

        # Update job to resubmitted
        return JobApprovalUseCase(self.request_scope).update_job_approval_status(
            submission.id,
            user_id=self.request_scope.user_id,
            is_admin_update=False,
            updates=AdminCreateApprovalUpdate(
                approval_status=JobApprovalStatus.RESUBMITTED,
                reason="Resubmitted by user",
            ),
        )

    def submit_many_jobs_for_approval(
        self, company_id: str, job_id_list: list[str]
    ) -> list[dict]:
        jobs_with_errors = []
        for job_id in job_id_list:
            try:
                self.submit_job_for_approval(company_id, job_id)
            except FailedToPostJobException as exc:
                jobs_with_errors.append({"job_id": job_id, "error": str(exc)})
        return jobs_with_errors

    def remove_job_submission(self, company_id: str, job_id: str) -> bool:
        admin_approval_repo = self.get_repository(
            Collection.ADMIN_JOB_APPROVALS, self.request_scope
        )
        submission = admin_approval_repo.get_one(company_id=company_id, job_id=job_id)
        JobApprovalUseCase(self.request_scope).update_job_approval_status(
            submission.id,
            user_id=self.request_scope.user_id,
            is_admin_update=False,
            updates=AdminCreateApprovalUpdate(
                approval_status=JobApprovalStatus.REMOVED_BY_USER,
                reason="Removed by user",
            ),
        )
        return True

    def unpost_job(self, company_id: str, job_id: str) -> Job:
        # Remove from algolia and update job history
        self.aloglia_jobs.delete_object(job_id)

        with self.request_scope.start_transaction(
            read_collections=[Collection.JOBS, Collection.ADMIN_JOB_APPROVALS],
            write_collections=[Collection.JOBS, Collection.ADMIN_JOB_APPROVALS],
        ) as transaction_scope:
            job_repo = self.get_repository(
                Collection.JOBS, transaction_scope, company_id
            )
            job_approval_repo = self.get_repository(
                Collection.ADMIN_JOB_APPROVALS, transaction_scope
            )
            submission: AdminJobPostApproval = job_approval_repo.get_one(
                company_id=company_id, job_id=job_id
            )
            JobApprovalUseCase(self.request_scope).update_job_approval_status(
                submission.id,
                user_id=self.request_scope.user_id,
                is_admin_update=False,
                updates=AdminCreateApprovalUpdate(
                    approval_status=JobApprovalStatus.UNPOSTED,
                    reason="Job Post Removed by user",
                ),
            )
            updated_job = job_repo.update_fields(job_id, is_live=False)
        return updated_job

    def update_job(
        self,
        company_id: str,
        job_id: str,
        updates: UserCreateJob = UserCreateJob(),
        **kwargs,
    ) -> Job:
        """This acts as both the normal update and an update by fields method"""
        updates_as_dict = updates.model_dump()
        updates_as_dict.update(kwargs)
        updates = UserCreateJob.model_validate(updates_as_dict)
        with self.request_scope.start_transaction(
            read_collections=[Collection.JOBS, Collection.ADMIN_JOB_APPROVALS],
            write_collections=[Collection.JOBS, Collection.ADMIN_JOB_APPROVALS],
        ) as transaction_scope:
            job_repo = self.get_repository(
                Collection.JOBS, transaction_scope, company_id
            )
            job_approval_repo = self.get_repository(
                Collection.ADMIN_JOB_APPROVALS, transaction_scope
            )

            # Check if job has been submitted
            try:
                submission: AdminJobPostApproval = job_approval_repo.get_one(
                    company_id=company_id, job_id=job_id
                )
            except EntityNotFound:
                return job_repo.update(job_id, updates)

            # If job is live, then reject the update
            job: Job = job_repo.get(job_id)
            if job.is_live:
                raise FailedToUpdateJobException(
                    f"Job {job_id} is live and can not be updated"
                )

            # If job is still pending, don't update status
            if submission.current_approval_status == JobApprovalStatus.PENDING:
                return job_repo.update(job_id, updates)

            # Otherwise, change job status to pending
            JobApprovalUseCase(transaction_scope).update_job_approval_status(
                submission.id,
                user_id=transaction_scope.user_id,
                is_admin_update=False,
                updates=AdminCreateApprovalUpdate(
                    approval_status=JobApprovalStatus.PENDING,
                    reason="Job details were updated by user",
                ),
            )

            # Finally, update the job
            updated_job: Job = job_repo.update(job_id, updates)
            new_job_score = updated_job.calculate_score()
            updated_job = job_repo.update_fields(job.id, job_score=new_job_score)

        return updated_job
