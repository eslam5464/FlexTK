import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Tuple

from b2sdk._internal.file_version import FileVersion  # noqa
from b2sdk.v2 import B2Api, B2RawHTTPApi, FileIdAndName, InMemoryAccountInfo
from b2sdk.v2.b2http import B2Http
from b2sdk.v2.bucket import Bucket
from b2sdk.v2.exception import NonExistentBucket
from lib.exceptions import (
    B2BucketNotFoundError,
    B2BucketNotSelectedError,
    BlackBlazeError,
)
from lib.schemas.black_blaze_bucket import ApplicationData
from pydantic import AnyUrl


class BucketTypeEnum(StrEnum):
    all_public = "allPublic"
    all_private = "allPrivate"


@dataclass(init=False)
class BlackBlaze:
    b2_raw: B2RawHTTPApi = field(default=B2RawHTTPApi(B2Http()))
    __bucket: Bucket | None = field(default=None)
    __b2_api: B2Api = field(default=B2Api(InMemoryAccountInfo()))

    def __init__(self, app_data: ApplicationData):
        """
        A class representing the BlackBlazeB2 client for interacting with the BlackBlaze B2 cloud storage service.
        It provides methods for interacting with the BlackBlaze B2 service, including authorization,
        selecting a bucket, and performing various operations on the selected bucket.
        :param app_data: Application data required to initiate black blaze connection
        :raise BlackBlazeError: Black blaze not authorized
        """
        try:
            self.__b2_api.authorize_account(
                realm="production",
                application_key_id=app_data.app_id,
                application_key=app_data.app_key,
            )
        except Exception as ex:
            raise BlackBlazeError(
                message=f"Could not authorize back blaze account",
                exception=ex,
            )

    @property
    def bucket(self):
        return self.__bucket

    def select_bucket(self, bucket_name):
        """
        Select a bucket in black blaze b2
        :param bucket_name: 'example-my-bucket-b2-1'  # must be unique in B2 (across all accounts!)
        """
        try:
            self.__b2_api.get_bucket_by_name(bucket_name)
        except NonExistentBucket as ex:
            raise B2BucketNotFoundError(
                message=f"While selecting the bucket {bucket_name}, the bucket does not exist",
                exception=ex,
            )
        except Exception as ex:
            raise BlackBlazeError(
                f"Error while selecting the bucket {bucket_name}, ex: {ex}",
            )

    def create_b2_bucket(self, bucket_name: str, bucket_type: BucketTypeEnum):
        """
        Create a bucket in black blaze b2
        :param bucket_name: 'example-my-bucket-b2-1'  # must be unique in B2 (across all accounts!)
        :param bucket_type: 'allPublic'  # or 'allPrivate'
        """
        try:
            bucket_type = str(bucket_type.value)
            self.__b2_api.create_bucket(name=bucket_name, bucket_type=bucket_type)
        except Exception as ex:
            raise BlackBlazeError(
                message=f"Could not create bucket {bucket_name}",
                exception=ex,
            )

    def delete_selected_bucket(self):
        """
        Delete the currently selected BlackBlaze B2 bucket.
        """
        self.__check_bucket_is_selected()

        try:
            bucket = self.__b2_api.get_bucket_by_name(self.__bucket.name)
            self.__b2_api.delete_bucket(bucket)
        except NonExistentBucket as ex:
            raise B2BucketNotFoundError(
                message=f"While deleting selected bucket {self.__bucket.name}, the bucket does not exist",
                exception=ex,
            )
        except Exception as ex:
            raise BlackBlazeError(
                f"Error while deleting selected bucket {self.__bucket.name}",
                exception=ex,
            )

    def update_selected_bucket(
        self,
        bucket_type: BucketTypeEnum | None = None,
        bucket_info: dict | None = None,
    ) -> Bucket:
        """
        Update the properties of the currently selected BlackBlaze B2 bucket.
        :param bucket_type: The new type of the bucket (e.g., BucketTypeEnum.ALL_PUBLIC).
        :param bucket_info: The info to store with the bucket
        :return: A Bucket object representing the updated bucket.
        """
        self.__check_bucket_is_selected()

        try:
            bucket = self.__b2_api.get_bucket_by_name(self.__bucket.name)
            bucket_type = bucket_type.value if isinstance(bucket_type, BucketTypeEnum) else None
            return bucket.update(
                bucket_type=bucket_type,
                bucket_info=bucket_info,
            )
        except NonExistentBucket as ex:
            raise BlackBlazeError(
                f"While updating selected bucket {self.__bucket.name}, the bucket does not exist, ex: {ex}",
            )
        except Exception as ex:
            raise BlackBlazeError(
                f"Error while updating selected bucket {self.__bucket.name}, ex: {ex}",
            )

    def upload_file(
        self,
        local_file_path: str,
        b2_file_name: str,
        file_info: dict | None = None,
    ) -> FileVersion:
        """
        Uploads a file to the selected BlackBlaze B2 bucket.
        :param local_file_path: a path to a file on local disk
        :param b2_file_name: a file name of the new B2 file
        :param file_info: a file info to store with the file or None to not store anything
        :return: A FileVersion object representing the uploaded file.
        """
        self.__check_bucket_is_selected()

        if file_info is None:
            file_info = {"scanned": "false"}

        try:
            bucket = self.__b2_api.get_bucket_by_name(self.__bucket.name)
            return bucket.upload_local_file(
                local_file=local_file_path,
                file_name=b2_file_name,
                file_info=file_info,
            )
        except Exception as ex:
            os.remove(local_file_path)
            raise BlackBlazeError(
                message=f"Error while uploading file '{local_file_path}'",
                exception=ex,
            )

    def get_download_url_by_name(
        self,
        file_name: str,
    ) -> str:
        """
        Gets the download url
        :param file_name: full path for the file
        :return: download url
        """
        self.__check_bucket_is_selected()

        bucket = self.__b2_api.get_bucket_by_name(self.__bucket.name)
        try:
            return bucket.get_download_url(file_name)
        except Exception as ex:
            raise BlackBlazeError(
                f"Error while getting download url for file name '{file_name}'",
                exception=ex,
            )

    def get_download_url_by_file_id(
        self,
        file_id: str,
    ) -> str:
        """
        Gets the download url using id for the file.
        :param file_id: file id in the selected bucket
        :return: download url
        """
        self.__check_bucket_is_selected()

        try:
            return self.__b2_api.get_download_url_for_fileid(file_id)
        except Exception as ex:
            raise BlackBlazeError(
                message=f"Error while getting download url for file with id '{file_id}'",
                exception=ex,
            )

    def delete_file(self, file_id: str, file_name: str) -> FileIdAndName:
        """
        Delete a file from the currently selected BlackBlaze B2 bucket.
        :param file_id: The ID of the file to be deleted.
        :param file_name: The name of the file to be deleted.
        :return: A FileIdAndName object representing the deleted file.
        """
        self.__check_bucket_is_selected()

        try:
            return self.__b2_api.delete_file_version(
                file_id=file_id,
                file_name=file_name,
            )
        except Exception as ex:
            raise BlackBlazeError(
                message=f"Error while deleting '{file_name}' with file id '{file_id}'",
                exception=ex,
            )

    def get_temp_download_link(
        self,
        url: AnyUrl,
        valid_duration_in_seconds: int = 900,
    ) -> Tuple[str, str]:
        """
        returns the download link and the authorization header token for the get request
        :param valid_duration_in_seconds: duration in seconds, default is 15 minutes
        :param url: download link with file id
        :return: download_url, auth_token
        """
        self.__check_bucket_is_selected()

        try:
            file_id = url.__str__().split("fileId=")[-1]
            file_info = self.__bucket.get_file_info_by_id(file_id)
            auth_token = self.__bucket.get_download_authorization(
                file_name_prefix=file_info.file_name,
                valid_duration_in_seconds=valid_duration_in_seconds,
            )
            download_url = self.__bucket.get_download_url(file_info.file_name)

            return download_url, auth_token
        except Exception as ex:
            raise BlackBlazeError(message=f"Can not get download url", exception=ex)

    def get_file_details_with_id(self, file_id: str) -> FileVersion:
        """
        Retrieve file details using the file ID.
        :param file_id: The ID of the file for which you want to retrieve details.
        :return: A FileVersion object representing the details of the specified file.
        """
        self.__check_bucket_is_selected()

        return self.__b2_api.get_file_info(file_id)

    def __check_bucket_is_selected(self):
        if not self.__bucket:
            raise B2BucketNotSelectedError(
                "No bucket is selected to perform this operation",
            )
