from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.admin.events import AdminEventProducer
from ajb.contexts.companies.jobs.models import Job, AlgoliaJobRecord
from ajb.exceptions import (
    MissingJobFieldsException,
    EntityNotFound,
    FailedToPostJobException,
)
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.vendor.algolia.repository import AlgoliaSearchRepository, AlgoliaIndex

from .models import (
    UpdateJobApprovalStatus,
    AdminCreateApprovalUpdate,
    AdminJobPostApproval,
    JobApprovalStatus,
)


class JobApprovalUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        aloglia_jobs: AlgoliaSearchRepository | None = None,
    ):
        self.request_scope = request_scope
        self.aloglia_jobs = aloglia_jobs or AlgoliaSearchRepository(AlgoliaIndex.JOBS)

    def _add_approval_history(
        self,
        submission_id: str,
        new_status: JobApprovalStatus,
        status_reason: str,
        updating_user_id: str,
        is_admin_update: bool,
        approval_object_to_update: AdminJobPostApproval,
    ):
        admin_approval_repo = self.get_repository(Collection.ADMIN_JOB_APPROVALS)
        status_update = UpdateJobApprovalStatus(
            approval_status=new_status,
            reason=status_reason,
            updated_by_id=updating_user_id,
            user_is_admin=is_admin_update,
        )

        # Update approval status
        approval_object_to_update.current_approval_status = new_status
        approval_object_to_update.current_reason = status_reason
        approval_object_to_update.history.append(status_update)
        admin_approval_repo.update(submission_id, approval_object_to_update)

    def update_job_approval_status(
        self,
        submission_id: str,
        user_id: str,
        is_admin_update: bool,
        updates: AdminCreateApprovalUpdate,
        auto_post_job: bool = True,
    ) -> AdminJobPostApproval:
        if is_admin_update:
            # Just make sure user is admin
            admin_user_repo = self.get_repository(Collection.ADMIN_USERS)
            assert admin_user_repo.get(user_id)

        admin_approval_repo = self.get_repository(Collection.ADMIN_JOB_APPROVALS)
        approval_object: AdminJobPostApproval = admin_approval_repo.get(submission_id)

        # Define new status update
        self._add_approval_history(
            submission_id=submission_id,
            new_status=updates.approval_status,
            status_reason=updates.reason,
            updating_user_id=self.request_scope.user_id,
            is_admin_update=is_admin_update,
            approval_object_to_update=approval_object,
        )

        # Create the company event based on the approval status
        if updates.approval_status == JobApprovalStatus.APPROVED and auto_post_job:
            self.post_job(approval_object.company_id, approval_object.job_id)
        elif updates.approval_status == JobApprovalStatus.REJECTED:
            AdminEventProducer(
                request_scope=self.request_scope, source_service=SourceServices.ADMIN
            ).admin_rejects_job_submission(
                company_id=approval_object.company_id,
                job_id=approval_object.job_id,
            )

        return approval_object

    def post_job(self, company_id: str, job_id: str) -> Job:
        with self.request_scope.start_transaction(
            read_collections=[Collection.JOBS],
            write_collections=[Collection.JOBS, Collection.ADMIN_JOB_APPROVALS],
        ) as transaction_scope:
            job_repo = self.get_repository(
                Collection.JOBS, transaction_scope, company_id
            )
            job: Job = job_repo.get(job_id)
            try:
                job.check_for_missing_fields()
            except MissingJobFieldsException as exc:
                raise FailedToPostJobException(exc.message)

            job_approval_repo = self.get_repository(
                Collection.ADMIN_JOB_APPROVALS, transaction_scope
            )
            try:
                submission: AdminJobPostApproval = job_approval_repo.get_one(
                    company_id=company_id, job_id=job_id
                )
            except EntityNotFound:
                raise FailedToPostJobException(
                    f"Job {job_id} has not been submitted for approval"
                )
            if submission.current_approval_status != JobApprovalStatus.APPROVED:
                raise FailedToPostJobException(
                    f"Job {job_id} has not been approved for posting"
                )

            updated_job = job_repo.update_fields(job_id, is_live=True, draft=False)

            # Update admin approval
            self._add_approval_history(
                submission_id=submission.id,
                new_status=JobApprovalStatus.POSTED,
                status_reason="Job was posted",
                updating_user_id=self.request_scope.user_id,
                is_admin_update=True,
                approval_object_to_update=submission,
            )

            # Add to algolia
            self.aloglia_jobs.create_object(
                job.id,
                AlgoliaJobRecord.convert_from_job_record(
                    job, "nice company", transaction_scope
                ).model_dump(),
            )
            # CompanyEventProducer(
            #     self.request_scope, SourceServices.API
            # ).job_submission_is_posted(job_id=job_id)
        return updated_job
