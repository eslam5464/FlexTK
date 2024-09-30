import logging
import math
import mimetypes
import os
from dataclasses import dataclass, field
from typing import Self

from google.api_core.exceptions import NotFound
from google.api_core.page_iterator import HTTPIterator
from google.cloud.storage import Bucket, Client
from lib.exceptions import GCSBucketNotFoundError, GCSBucketNotSelectedError
from lib.schemas.google_bucket import (
    BucketFile,
    BucketFolder,
    DownloadBucketFile,
    ServiceAccount,
)
from lib.utils.network import get_upload_time

logger = logging.getLogger(__name__)


@dataclass(init=False)
class GCS:
    __client: Client | None = field(default=None)
    __bucket: Bucket | None = field(default=None)

    def __init__(
        self,
        bucket_name: str,
        service_account_info: ServiceAccount | str,
    ):
        """
        A class representing the Google client for interacting with the Google cloud storage service.
        It provides methods for interacting with the Google cloud service.
        :param service_account_info: Service account information schema or the path to the service account
        :raise GCSBucketNotFoundError: Bucket not found
        """
        if isinstance(service_account_info, str):
            self.__client = Client.from_service_account_json(service_account_info)
        elif isinstance(service_account_info, ServiceAccount):
            self.__client = Client.from_service_account_info(
                {
                    "type": "service_account",
                    "project_id": service_account_info.project_id,
                    "private_key_id": service_account_info.private_key_id,
                    "private_key": service_account_info.private_key,
                    "client_email": service_account_info.client_email,
                    "client_id": service_account_info.client_id,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                },
            )
        else:
            raise NotImplementedError("Parameter not supported")

        self.set_bucket(bucket_name=bucket_name)

    @property
    def client(self) -> Client | None:
        return self.__client

    @property
    def bucket(self) -> Bucket | None:
        return self.__bucket

    def set_bucket(
        self,
        bucket_name: str,
    ) -> Self:
        """
        Set the bucket
        :param bucket_name: Name of the bucket in GCS
        :return: The GCS instance.
        :raise GCSBucketNotFoundError: Bucket not found
        """
        try:
            self.__bucket = self.__client.get_bucket(bucket_name)
        except NotFound as ex:
            raise GCSBucketNotFoundError(message="Bucket not found", exception=ex)

        return Self

    def upload_file(
        self,
        file_path: str,
        bucket_folder_path: str,
        timeout: int = 300,
        calculate_upload_estimation: bool = False,
    ) -> BucketFile | None:
        """
        Uploads a file to google bucket
        :param file_path: File path to upload to google bucket
        :param bucket_folder_path: Name of the folder inside the bucket to upload e.g. path/to/folder/in/bucket/
        :param timeout: The maximum time, in seconds, to wait for the upload to complete. Default is 300 seconds.
        :param calculate_upload_estimation: Flag to enable/disable upload time estimation.
        :return: A BucketFile object contains the uploaded file data or None
        :raise GCSBucketNotSelectedError: No bucket is selected
        :raise ValueError: If the file is not found at the specified path.
        """
        self.__check_bucket_is_selected()

        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found")

        if not bucket_folder_path.endswith("/"):
            bucket_folder_path += "/"

        if calculate_upload_estimation:
            file_size = math.ceil(os.path.getsize(file_path) / (1024 * 1024))
            calculated_upload_time = get_upload_time(
                file_size_mb=file_size,
            )
            calculated_upload_time = math.ceil(calculated_upload_time)
            logger.info(
                f"Uploading {os.path.basename(file_path)} will " f"take an estimated {calculated_upload_time} seconds",
            )

            if calculated_upload_time > timeout:
                timeout = int(calculated_upload_time)

        filename = os.path.basename(file_path)
        blob = self.__bucket.blob(bucket_folder_path + filename)
        content_type, _ = mimetypes.guess_type(filename)
        blob.upload_from_filename(filename=file_path, content_type=content_type, timeout=timeout)

        return self.get_file(bucket_folder_path)

    def get_file(
        self,
        file_path_in_bucket: str,
    ) -> BucketFile | None:
        """
        Retrieves file information from a Google Cloud Storage bucket.
        :param file_path_in_bucket: The file's full path inside the bucket, e.g., 'folder/file.txt'.
        :return: A BucketFile object or None if the file does not exist.
        :raises GCSBucketNotSelectedError: If no bucket is selected for the operation.
        """
        self.__check_bucket_is_selected()
        blob = self.__bucket.get_blob(prefix=file_path_in_bucket)

        if blob is None:
            return blob

        return BucketFile(
            id=blob.id,
            basename=os.path.basename(blob.name),
            file_path_in_bucket=blob.name,
            bucket_name=self.__bucket.name,
            public_url=blob.public_url,
            authenticated_url=blob.public_url.replace("googleapis", "cloud.google"),
            size_bytes=blob.size,
            creation_date=blob.time_created,
            modification_date=blob.updated,
            md5_hash=blob.md5_hash,
            crc32c_checksum=blob.crc32c,
            content_type=blob.content_type,
        )

    def get_files(
        self,
        folder_path_in_bucket: str,
    ) -> list[BucketFile]:
        """
        Lists all the blobs in the bucket.
        :param folder_path_in_bucket: Name of the folder inside the bucket e.g. path/to/folder/in/bucket/
        :return: List of BucketFile contain the files details
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        if not folder_path_in_bucket.endswith("/"):
            folder_path_in_bucket += "/"

        blobs = self.__bucket.list_blobs(prefix=folder_path_in_bucket)
        folder_path_in_bucket = "" if not folder_path_in_bucket else folder_path_in_bucket

        return [
            BucketFile(
                id=blob.id,
                basename=blob.name.replace(folder_path_in_bucket, ""),
                file_path_in_bucket=blob.name,
                bucket_name=self.__bucket.name,
                public_url=blob.public_url,
                authenticated_url=blob.public_url.replace("googleapis", "cloud.google"),
                size_bytes=blob.size,
                creation_date=blob.time_created,
                modification_date=blob.updated,
                md5_hash=blob.md5_hash,
                crc32c_checksum=blob.crc32c,
                content_type=blob.content_type,
            )
            for blob in blobs
            if blob.name != folder_path_in_bucket
        ]

    def create_folder(
        self,
        folder_name: str,
    ) -> Self:
        """
        Creates a folder in the specified bucket
        :param folder_name: Name of the folder that will be created
        :return: The GCS instance.
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        if not folder_name.endswith("/"):
            folder_name += "/"

        blob = self.__bucket.blob(folder_name)
        blob.upload_from_string(
            "",
            content_type="application/x-www-form-urlencoded;charset=UTF-8",
        )
        logger.info(f"Created folder {folder_name} in bucket {self.__bucket.name}")

        return self

    def download_multiple_files(
        self,
        files_to_download: list[DownloadBucketFile],
    ) -> Self:
        """
        Download multiple files from bucket's path to disk
        :param files_to_download: List of file schemas to download
        :return: The GCS instance.
        :raise NotADirectoryError: Download directory not found
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        for file_entry in files_to_download:
            logger.info(
                msg=f"Downloading file {file_entry.bucket_path}",
                extra={"download_location": file_entry.download_directory},
            )
            blob = self.__bucket.blob(file_entry.bucket_path)
            destination_file_name = os.path.join(
                file_entry.download_directory,
                file_entry.filename_on_disk,
            )
            blob.download_to_filename(destination_file_name)

        return self

    def delete_files(
        self,
        list_of_files: list[str],
    ) -> Self:
        """
        Delete list of files from the specified bucket path
        :param list_of_files: files to be deleted
        :return: The GCS instance.
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        for file_entry in list_of_files:
            blob = self.__bucket.blob(file_entry)
            blob.delete()
            logger.info(
                msg=f"Deleted file {file_entry} in bucket {self.__bucket.name}",
            )

        return self

    def get_folders(self, bucket_folder_path: str) -> list[BucketFolder]:
        """
        Retrieves a list of folder names from the specified Google Cloud Storage bucket path.
        :param bucket_folder_path: The path of the folder in the GCS bucket to search for subfolders.
        :return: A list of BucketFolder objects found under the specified `bucket_folder_path`.
        """

        def _item_to_value(iterator_item, item):
            return item

        if not bucket_folder_path.endswith("/"):
            bucket_folder_path += "/"

        extra_params = {
            "projection": "noAcl",
            "prefix": bucket_folder_path,
            "delimiter": "/",
        }
        path = "/b/" + self.bucket.name + "/o"

        iterator = HTTPIterator(
            client=self.client,
            api_request=self.client._connection.api_request,  # noqa
            path=path,
            items_key="prefixes",
            item_to_value=_item_to_value,
            extra_params=extra_params,
        )

        return [
            BucketFolder(
                name=iter_entry.split(bucket_folder_path)[-1][:-1],
                bucket_folder_path=bucket_folder_path,
            )
            for iter_entry in iterator
        ]

    def __check_bucket_is_selected(self):
        """
        Checks whether a Google Cloud Storage bucket has been selected for operations.
        This method raises a `GCSBucketNotSelectedError` if no bucket has been selected,
        preventing any further actions that require a bucket.
        :raises GCSBucketNotSelectedError: If no bucket is selected.
        """
        if not self.__bucket:
            raise GCSBucketNotSelectedError(
                "No bucket is selected to perform this operation",
            )
