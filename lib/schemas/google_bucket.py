import base64
import os
from datetime import datetime

from pydantic import HttpUrl, field_validator

from .base import BaseSchema


class ServiceAccount(BaseSchema):
    private_key: str
    private_key_id: str
    project_id: str
    client_email: str
    client_id: str


class DownloadBucketFile(BaseSchema):
    bucket_path: str
    filename_on_disk: str
    download_directory: str

    @field_validator("download_directory")
    def directory_must_exist(cls: "DownloadBucketFile", value: str) -> str:
        if not os.path.isdir(value):
            raise NotADirectoryError(
                f"Directory '{value}' does not exist to download the file into it",
            )

        return value


class BucketFile(BaseSchema):
    id: str
    basename: str
    file_path_in_bucket: str
    bucket_name: str
    authenticated_url: HttpUrl
    public_url: HttpUrl
    size_bytes: int
    md5_hash: str
    crc32c_checksum: int
    content_type: str
    metadata: str
    creation_date: datetime
    modification_date: datetime

    @field_validator("md5_hash")
    def decode_md5_hash(cls, value: str) -> str:
        decoded_bytes = base64.b64decode(value)

        return decoded_bytes.hex()

    @field_validator("crc32c_checksum", mode="before")
    def decode_crc32c_checksum(cls, value: str) -> int:
        decoded_bytes = base64.b64decode(value)

        return int.from_bytes(decoded_bytes, byteorder="big")


class BucketFolder(BaseSchema):
    name: str
    bucket_folder_path: str
