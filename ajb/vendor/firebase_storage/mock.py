from google.cloud.storage import Bucket


class MockStorageBlob:
    def __init__(self, *args, **kwargs):
        ...

    def upload_from_string(self, *args, **kwargs):
        ...

    def upload_from_filename(self, *args, **kwargs):
        ...

    def make_public(self, *args, **kwargs):
        ...

    def make_private(self, *args, **kwargs):
        ...

    def download_to_filename(self, *args, **kwargs):
        ...

    def download_as_bytes(self, *args, **kwargs):
        ...

    def delete(self, *args, **kwargs):
        ...

    @property
    def public_url(self):
        return "https://mocked-url.com"


class MockFirebaseStorageClient(Bucket):
    # pylint: disable=super-init-not-called
    def __init__(self, *args, **kwargs):
        self.blobs = {}

    # pylint: disable=arguments-differ
    def blob(self, remote_file_path: str) -> MockStorageBlob:
        blob = MockStorageBlob(remote_file_path)
        self.blobs[remote_file_path] = blob
        return blob
