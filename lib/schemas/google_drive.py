import os

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


class DriveFileUpload(BaseMetadata):
    parent_folder_id: str
    filename_on_drive: str
    file_path: str

    @field_validator("file_path")
    def validate_path(cls, value: str):
        if not os.path.isfile(value):
            raise FileNotFoundError(f"File not found in {value}")

        return value


class DriveFile(BaseMetadata):
    id: str
    filename: str
    parent_folder_id: str | None
