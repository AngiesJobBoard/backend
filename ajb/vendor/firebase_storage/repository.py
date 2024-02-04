from google.cloud.storage import Bucket

from .client_factory import FirebaseStorageClientFactory


class FirebaseStorageRepository:
    def __init__(self, client: Bucket | None = None):
        self._client = client or FirebaseStorageClientFactory.get_client()

    def upload_bytes(
        self,
        file_bytes: bytes,
        content_type: str,
        remote_file_path: str,
        publicly_accessible: bool = False,
    ) -> str:
        blob = self._client.blob(remote_file_path)
        blob.upload_from_string(data=file_bytes, content_type=content_type)
        if publicly_accessible:
            blob.make_public()
        return blob.public_url

    def update_file_public_access(
        self, remote_file_path, publicly_accessible: bool = False
    ) -> str:
        blob = self._client.blob(remote_file_path)
        if publicly_accessible:
            blob.make_public()
        else:
            blob.make_private()
        return blob.public_url

    def get_file_bytes(self, remote_file_path) -> bytes:
        blob = self._client.blob(remote_file_path)
        return blob.download_as_bytes()

    def delete_file(self, remote_file_path) -> None:
        blob = self._client.blob(remote_file_path)
        blob.delete()
