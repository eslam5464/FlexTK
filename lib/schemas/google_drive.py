import os
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import AnyHttpUrl, EmailStr, Field, field_validator

from .base import BaseSchema


class DrivePermissionRoleEnum(StrEnum):
    owner = "owner"
    organizer = "organizer"
    file_organizer = "fileOrganizer"
    writer = "writer"
    commenter = "commenter"
    reader = "reader"


class DriveWebData(BaseSchema):
    client_id: str
    project_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_secret: str


class DriveCredentials(BaseSchema):
    """
    - This schema represents the credentials obtained from the Google
    Developer Console following the instructions outlined in the
    Google Drive API Python quickstart guide:
    https://developers.google.com/drive/api/quickstart/python
    - You can check the available scopes from this guide:
    https://developers.google.com/drive/api/guides/api-specific-auth
    """

    web: DriveWebData
    scopes: list[str] = Field(default=["https://www.googleapis.com/auth/drive"])


class DriveFolder(BaseSchema):
    id: str
    name: str
    parent_ids: list[str]
    in_trash: bool


class DriveBlobPermissions(BaseSchema):
    public_read: bool = False
    reader_email: EmailStr | None = None
    writer_email: EmailStr | None = None


class DriveFileUpload(BaseSchema):
    parent_folder_id: str
    filename_on_drive: str
    file_path: str
    permissions: DriveBlobPermissions = Field(default=DriveBlobPermissions())

    @field_validator("file_path")
    def validate_path(cls, value: str):
        if not os.path.isfile(value):
            raise FileNotFoundError(f"File not found in {value}")

        return value


class DriveFileDownload(BaseSchema):
    file_id: str
    save_path: str

    @field_validator("save_path")
    def validate_path(cls, value: str):
        if not os.path.isdir(value):
            raise NotADirectoryError(f"No directory exists in {value}")

        return value


class DriveUser(BaseSchema):
    is_current_user: bool = Field(alias="me")
    kind: str = Field(alias="kind", exclude=True)
    name: str = Field(alias="displayName")
    permission_id: str = Field(alias="permissionId")
    email: str | None = Field(alias="emailAddress")
    photo_url: AnyHttpUrl | None = Field(alias="photoLink")


class DrivePermissionDetail(BaseSchema):
    permission_type: str = Field(alias="permissionType")
    inherited_from: str = Field(alias="inheritedFrom")
    role: str
    inherited: bool


class DriveTeamDrivePermissionDetail(BaseSchema):
    team_drive_permission_type: str = Field(alias="teamDrivePermissionType")
    inherited_from: str = Field(alias="inheritedFrom")
    role: str
    inherited: bool


class DrivePermission(BaseSchema):
    id: str
    type: str
    kind: str
    display_name: str = Field(alias="displayName")
    email_address: str = Field(alias="emailAddress")
    role: DrivePermissionRoleEnum
    photo_url: AnyHttpUrl = Field(alias="photoLink")
    allow_file_discovery: bool | None = Field(alias="allowFileDiscovery", default=None)
    domain: str | None = None
    expiration_time: str | None = Field(alias="expirationTime", default=None)
    deleted: bool
    view: str | None = None
    pending_owner: bool = Field(alias="pendingOwner")
    team_drive_permission_details: list[DriveTeamDrivePermissionDetail] | None = Field(
        alias="teamDrivePermissionDetails",
        default=None,
    )
    permission_details: list[DrivePermissionDetail] | None = Field(alias="permissionDetails", default=None)

    @field_validator("role", mode="before")
    def parse_role(cls, value: str):
        return DrivePermissionRoleEnum(value)


class DriveFile(BaseSchema):
    id: str
    filename: str
    original_filename: str | None
    thumbnail_url: str | None
    thumbnail_large_url: str | None
    extension: str | None
    size_bytes: int | None
    mimeType: str
    in_trash: bool
    parent_folder_ids: list[str]
    version: int
    creation_timestamp: datetime
    modification_timestamp: datetime
    is_shared: bool
    owners: list[DriveUser]
    permissions: list[DrivePermission]

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

        if "." in value and value[0] == ".":
            return value

        return "." + value
