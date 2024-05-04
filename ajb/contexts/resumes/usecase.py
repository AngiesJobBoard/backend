from datetime import datetime
from ajb.base import BaseUseCase, RequestScope, Collection
from ajb.utils import random_salt
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository

from .models import Resume, CreateResume, UserCreateResume


class ResumeUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        storage: FirebaseStorageRepository | None = None,
    ):
        self.request_scope = request_scope
        self.storage_repo = storage or FirebaseStorageRepository()

    def _create_resume_file_path(self, company_id: str, job_id: str):
        return f"{company_id}/{job_id}/resumes/{int(datetime.now().timestamp())}-{random_salt()}"

    def create_resume(self, data: UserCreateResume) -> Resume:
        remote_file_path = self._create_resume_file_path(data.company_id, data.job_id)
        resume_url = self.storage_repo.upload_bytes(
            data.resume_data, data.file_type, remote_file_path, publicly_accessible=True
        )
        resume_repo = self.get_repository(Collection.RESUMES)
        return resume_repo.create(
            CreateResume(
                remote_file_path=remote_file_path,
                resume_url=resume_url,
                file_name=data.file_name,
                company_id=data.company_id,
                job_id=data.job_id,
                file_type=data.file_type,
            )
        )

    def delete_resume(self, resume_id: str) -> bool:
        resume_repo = self.get_repository(Collection.RESUMES)
        resume: Resume = resume_repo.get(resume_id)
        self.storage_repo.delete_file(resume.remote_file_path)
        resume_repo.delete(resume_id)
        return True

    def update_resume(self, resume_id: str, data: UserCreateResume) -> Resume:
        resume_repo = self.get_repository(Collection.RESUMES)
        resume: Resume = resume_repo.get(resume_id)
        self.storage_repo.upload_bytes(
            data.resume_data,
            data.file_type,
            resume.remote_file_path,
            publicly_accessible=True,
        )
        return resume_repo.update(
            resume_id,
            CreateResume(
                resume_url=resume.resume_url,
                file_type=data.file_type,
                remote_file_path=resume.remote_file_path,
                file_name=data.file_name,
                company_id=data.company_id,
                job_id=data.job_id,
            ),
        )
