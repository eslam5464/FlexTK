import os

from pydantic import field_validator

from .base import BaseMetadata


class DriveServiceAccount(BaseMetadata):
    private_key: str
    private_key_id: str
    project_id: str
    client_email: str
    client_id: str
    client_x509_cert_url: str


class DriveFolder(BaseMetadata):
    id: str
    name: str
    parent_ids: list[str]


class DriveFileUpload(BaseMetadata):
    parent_folder_id: str
    filename_on_drive: str
    file_path: str

    @field_validator("file_path")
    def validate_path(cls, value: str):
        if os.path.isfile(value):
            raise FileNotFoundError(f"File not found in {value}")

        return value


class DriveFile(BaseMetadata):
    id: str
    filename: str
    parent_folder_id: str | None
