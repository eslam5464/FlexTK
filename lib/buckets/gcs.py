import mimetypes
import os
from dataclasses import dataclass, field

from google.api_core.exceptions import NotFound
from google.api_core.page_iterator import HTTPIterator
from google.cloud.storage import Bucket, Client
from lib.exceptions import GCSBucketNotFoundError, GCSBucketNotSelectedError
from lib.schemas.google_bucket import DownloadMultiFiles, ServiceAccount
from lib.utils.misc import validate_text


@dataclass(init=False)
class GCS:
    __client: Client | None = field(default=None)
    __bucket: Bucket | None = field(default=None)

    def __init__(
        self,
        bucket_name: str,
        service_account_json_path: str | None = None,
        service_account_info: ServiceAccount | None = None,
    ):
        """
        A class representing the Google client for interacting with the Google cloud storage service.
        It provides methods for interacting with the Google cloud service.
        :param service_account_json_path: Name of the file to upload
        :param service_account_info: Service account information schema
        :raise ValueError: Both service_account_info and service_account_json_path are None or both have values
        :raise GCSBucketNotFoundError: Bucket not found
        """
        if service_account_info is None and service_account_json_path is None:
            raise ValueError(
                "Both json path and information for service account parameters are None, "
                "only one of them should be None",
            )
        elif service_account_info and service_account_json_path:
            raise ValueError(
                "Both json path and information for service account parameters has values, "
                "only one of then should have a value",
            )

        if service_account_json_path is not None:
            self.__client = Client.from_service_account_json(service_account_json_path)
        elif service_account_info is not None:
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
    ) -> None:
        """
        Set the bucket
        :param bucket_name: Name of the bucket in GCS
        :return: None
        :raise GCSBucketNotFoundError: Bucket not found
        """
        try:
            self.__bucket = self.__client.get_bucket(bucket_name)
        except NotFound as ex:
            raise GCSBucketNotFoundError(message="Bucket not found", exception=ex)

    @staticmethod
    def _validate_bucket_folder_name(folder_name: str):
        """
        Validate the folder name for bucket
        :param folder_name: Name of the folder to be validated
        :return: None
        :raise ValueError: folder_path_in_bucket must contain forward slash '/' at the end and not at the beginning
        """
        folder_path_regex = r"^[^/].*\/$"

        if folder_name and not validate_text(folder_name, folder_path_regex):
            raise ValueError(
                "folder_path_in_bucket should have '/' at the end and not at the beginning",
            )

    def upload_file(
        self,
        file_path: str,
        bucket_folder_path: str | None = None,
    ) -> str:
        """
        Uploads a file to google bucket
        :param file_path: File path to upload to google bucket
        :param bucket_folder_path: Name of the folder inside the bucket to upload e.g. path/to/folder/in/bucket/
        :return: URL of the uploaded file
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        if not os.path.exists(file_path):
            raise ValueError(f"File {file_path} not found")

        if not bucket_folder_path.endswith("/"):
            bucket_folder_path += "/"

        filename = os.path.basename(file_path)
        blob = self.__bucket.blob(bucket_folder_path + filename)
        content_type = mimetypes.guess_type(filename)[0]

        with open(file_path, "rb") as file_data:
            blob.upload_from_string(data=file_data.read(), content_type=content_type)

        return blob.public_url.replace("googleapis", "cloud.google")

    def get_files(
        self,
        folder_path_in_bucket: str | None = None,
    ) -> list[str]:
        """
        Lists all the blobs in the bucket.
        :param folder_path_in_bucket: Name of the folder inside the bucket e.g. path/to/folder/in/bucket/
        :return: List of URL of the uploaded file
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        if not folder_path_in_bucket.endswith("/"):
            folder_path_in_bucket += "/"

        blobs = self.__bucket.list_blobs(prefix=folder_path_in_bucket)
        folder_path_in_bucket = "" if not folder_path_in_bucket else folder_path_in_bucket

        return [blob.name.replace(folder_path_in_bucket, "") for blob in blobs if blob.name != folder_path_in_bucket]

    def create_folder(
        self,
        folder_name: str,
    ) -> None:
        """
        Creates a folder in the specified bucket
        :param folder_name: Name of the folder that will be created, the name must end with forward slash '/'
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        if not folder_name.endswith("/"):
            folder_name += "/"

        blob = self.__client.bucket(self.__bucket.name).blob(folder_name)
        blob.upload_from_string(
            "",
            content_type="application/x-www-form-urlencoded;charset=UTF-8",
        )

    def download_multiple_files(
        self,
        files_to_download: list[DownloadMultiFiles],
    ) -> None:
        """
        Download multiple files from bucket's path to disk
        :param files_to_download: List of file schemas to download
        :return: None
        :raise NotADirectoryError: Download directory not found
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        for file_entry in files_to_download:
            if not os.path.isdir(file_entry.download_directory):
                raise NotADirectoryError(
                    f"Directory '{file_entry.download_directory}' does not exist to download the file into it",
                )

            blob = self.__bucket.blob(file_entry.bucket_path)
            destination_file_name = os.path.join(
                file_entry.download_directory,
                file_entry.filename_on_disk,
            )
            blob.download_to_filename(destination_file_name)

    def delete_files(
        self,
        list_of_files: list[str],
    ) -> None:
        """
        Delete list of files from the specified bucket path
        :param list_of_files: files to be deleted
        :raise GCSBucketNotSelectedError: No bucket is selected
        """
        self.__check_bucket_is_selected()

        for file_entry in list_of_files:
            blob = self.__bucket.blob(file_entry)
            blob.delete()

    def get_folders(self, bucket_folder_path: str) -> list[str]:
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

        return [iter_entry.split(bucket_folder_path)[-1][:-1] for iter_entry in iterator]

    def __check_bucket_is_selected(self):
        if not self.__bucket:
            raise GCSBucketNotSelectedError(
                "No bucket is selected to perform this operation",
            )
