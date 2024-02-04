from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.vendor.firebase_storage.client_factory import FirebaseStorageClientFactory


class TestFirebaseStorage:
    client = FirebaseStorageClientFactory._return_mock()
    repo = FirebaseStorageRepository(client)

    def test_upload_bytes(self):
        self.repo.upload_bytes(
            file_bytes=b"test",
            content_type="test",
            remote_file_path="test",
        )

    def test_update_file_access(self):
        self.repo.update_file_public_access("test", True)
        self.repo.update_file_public_access("test", False)

    def test_get_file_bytes(self):
        self.repo.get_file_bytes("test")

    def test_delete_file(self):
        self.repo.delete_file("test")
