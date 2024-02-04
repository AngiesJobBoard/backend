from datetime import datetime

from ajb.base import BaseUseCase, RequestScope, Collection
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

    def _create_file_path(self, user_id: str):
        return f"{user_id}/resumes/{int(datetime.now().timestamp())}"

    def create_user_resume(self, user_id, data: UserCreateResume) -> Resume:
        resume_repo = self.get_repository(
            Collection.RESUMES, self.request_scope, parent_id=user_id
        )
        remote_file_path = self._create_file_path(user_id)
        resume_url = self.storage_repo.upload_bytes(
            data.resume_data, data.file_type, remote_file_path, True
        )
        return resume_repo.create(
            CreateResume(
                resume_url=resume_url,
                remote_file_path=remote_file_path,
                **data.model_dump(),
            )
        )

    def delete_user_resume(self, user_id: str, resume_id: str) -> bool:
        resume_repo = self.get_repository(
            Collection.RESUMES, self.request_scope, parent_id=user_id
        )
        resume: Resume = resume_repo.get(resume_id)
        self.storage_repo.delete_file(resume.remote_file_path)
        resume_repo.delete(resume_id)
        return True

    def update_user_resume(
        self, user_id, resume_id: str, data: UserCreateResume
    ) -> Resume:
        resume_repo = self.get_repository(
            Collection.RESUMES, self.request_scope, parent_id=user_id
        )
        resume: Resume = resume_repo.get(resume_id)
        self.storage_repo.upload_bytes(
            data.resume_data, data.file_type, resume.remote_file_path, True
        )
        return resume_repo.update(
            resume_id,
            CreateResume(
                resume_url=resume.resume_url,
                remote_file_path=resume.remote_file_path,
                file_name=data.file_name,
            ),
        )
