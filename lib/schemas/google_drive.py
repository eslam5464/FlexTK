import os
from datetime import datetime
from typing import Any

from pydantic import field_validator

from .base import BaseMetadata


class DriveWebData(BaseMetadata):
    client_id: str
    project_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_secret: str


class DriveCredentials(BaseMetadata):
    """
    - This schema represents the credentials obtained from the Google
    Developer Console following the instructions outlined in the
    Google Drive API Python quickstart guide:
    https://developers.google.com/drive/api/quickstart/python
    - You can check the available scopes from this guide:
    https://developers.google.com/drive/api/guides/api-specific-auth
    """

    web: DriveWebData
    scopes: list[str] | None = None


class DriveFolder(BaseMetadata):
    id: str
    name: str
    parent_ids: list[str]
    in_trash: bool


class DriveFileUpload(BaseMetadata):
    parent_folder_id: str
    filename_on_drive: str
    file_path: str

    @field_validator("file_path")
    def validate_path(cls, value: str):
        if not os.path.isfile(value):
            raise FileNotFoundError(f"File not found in {value}")

        return value


class DriveFileDownload(BaseMetadata):
    file_id: str
    save_path: str

    @field_validator("save_path")
    def validate_path(cls, value: str):
        if not os.path.isdir(value):
            raise NotADirectoryError(f"No directory exists in {value}")

        return value


class DriveFile(BaseMetadata):
    id: str
    filename: str
    original_filename: str | None
    extension: str | None
    size_bytes: int | None
    mimeType: str
    in_trash: bool
    parent_folder_ids: list[str]
    version: int
    creation_timestamp: datetime
    modification_timestamp: datetime
    is_shared: bool

    @field_validator("creation_timestamp", "modification_timestamp", mode="before")
    def validate_timestamps(cls, value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")

    @field_validator("version", "size_bytes", mode="before")
    def parse_to_int(cls, value: Any):
        if value is None:
            return value

        return int(value)

    @field_validator("extension")
    def parse_extension(cls, value: str | None):
        if not value:
            return value

        return "." + value
