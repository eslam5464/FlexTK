from .base import BaseMetadata


class ServiceAccount(BaseMetadata):
    private_key: str
    private_key_id: str
    project_id: str
    client_email: str
    client_id: str


class DownloadMultiFiles(BaseMetadata):
    bucket_path: str
    filename_on_disk: str
    download_directory: str
