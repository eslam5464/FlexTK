from datetime import datetime

from pydantic import HttpUrl

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


class UploadedFile(BaseMetadata):
    file_disk_path: str
    authenticated_url: str
    bucket_folder_path: HttpUrl


class BucketFile(BaseMetadata):
    id: str
    basename: str
    file_path_in_bucket: str
    bucket_name: str
    authenticated_url: str
    public_url: str
    size_bytes: int
    md5_hash: str
    creation_date: datetime
    modification_date: datetime
