import logging
import os
from pathlib import Path
from typing import Self

import boto3
from botocore.client import BaseClient, ClientError
from botocore.exceptions import NoCredentialsError
from lib.exceptions import AWSBucketNotFoundError, AWSError, AWSNoCredentialsError
from lib.schemas.aws_bucket import AccessData, BucketData, BucketFile

logger = logging.getLogger(__name__)


class AWS:
    def __init__(self, bucket_data: BucketData, access_data: AccessData):
        """
        Initializes the AWS class with bucket and access data, creating an S3 client.
        :param bucket_data: Data about the S3 bucket, including name and region.
        :param access_data: AWS access credentials containing access key and secret key.
        :raises AWSBucketNotFoundError: If the specified bucket does not exist.
        """
        self.__bucket_data = bucket_data
        self.__access_data = access_data
        self.__client = self.__get_client()
        self.check_bucket(self.__bucket_data.bucket_name)

    @property
    def client(self) -> BaseClient:
        """
        Returns the S3 client instance created for AWS operations.
        :return: The boto3 S3 client instance.
        """
        return self.__client

    def check_bucket(
        self,
        bucket_name: str,
    ) -> Self:
        """
        Verifies that the specified S3 bucket exists by performing a head request.
        :param bucket_name: The name of the S3 bucket to check.
        :return: The current instance of the AWS class.
        :raises AWSBucketNotFoundError: If the bucket does not exist or is inaccessible.
        """
        try:
            self.__client.head_bucket(Bucket=bucket_name)
        except ClientError as err:
            raise AWSBucketNotFoundError(message="Bucket not found", exception=err)

        return self

    def upload_files(
        self,
        file_path_on_disk: str,
        object_name: str | None = None,
    ) -> Self:
        """
        Uploads a file from local disk to the specified S3 bucket.
        :param file_path_on_disk: The local file path of the file to upload.
        :param object_name: Optional custom name for the file in the bucket; defaults to the file's basename.
        :return: The current instance of the AWS class.
        :raises FileNotFoundError: If the local file does not exist.
        :raises AWSError: If an error occurs during the upload process.
        """
        if not Path(file_path_on_disk).is_file():
            raise FileNotFoundError(f"File not found in {file_path_on_disk}")

        object_name = object_name or os.path.basename(file_path_on_disk)
        s3_object_path = f"folder/{object_name}"
        bucket_name = self.__bucket_data.bucket_name

        try:
            self.__client.upload_file(file_path_on_disk, bucket_name, s3_object_path)
            logger.info(
                msg=f"Uploaded {file_path_on_disk} to S3 at {bucket_name}/{s3_object_path}",
                extra={"file_location": file_path_on_disk, "bucket_path": f"{bucket_name}/{s3_object_path}"},
            )
        except ClientError as err:
            logger.error("Upload failed", extra={"error": err})
            raise AWSError("Failed to upload file to S3", exception=err)

        return self

    def get_file(self, file_path_in_bucket: str) -> BucketFile | None:
        """
        Retrieves metadata for a file stored in the specified S3 bucket.
        :param file_path_in_bucket: The path of the file within the S3 bucket.
        :return: A BucketFile object with file metadata if the file exists, else None.
        :raises AWSError: If an error occurs while accessing the file in the bucket.
        """
        bucket_name = self.__bucket_data.bucket_name

        try:
            self.__client.head_object(Bucket=bucket_name, Key=file_path_in_bucket)
        except ClientError as err:
            if err.response["Error"]["Code"] == "404":
                return None
            else:
                raise AWSError(message="Error while searching for file", exception=err)

        file_metadata = self.__client.get_object(Bucket=bucket_name, Key=file_path_in_bucket)

        return BucketFile(
            id=file_metadata["ETag"],
            basename=Path(file_path_in_bucket).name,
            extension=Path(file_path_in_bucket).suffix,
            file_path_in_bucket=file_path_in_bucket,
            bucket_name=bucket_name,
            public_url=f"https://{bucket_name}.s3.amazonaws.com/{file_path_in_bucket}",
            size_bytes=file_metadata["ContentLength"],
            modification_date=file_metadata["LastModified"],
            content_type=file_metadata["ContentType"],
        )

    def __get_client(self) -> BaseClient:
        """
        Creates and returns an S3 client with the provided AWS credentials.
        :return: A boto3 S3 client instance.
        :raises AWSNoCredentialsError: If AWS credentials are malformed or missing.
        """
        try:
            client: BaseClient = boto3.client(
                "s3",
                region_name=self.__bucket_data.region_name,
                aws_access_key_id=self.__access_data.access_key,
                aws_secret_access_key=self.__access_data.secret_key,
            )
        except NoCredentialsError:
            logging.error("AWS credentials are malformed or missing.")
            raise AWSNoCredentialsError("AWS credentials are malformed or missing.")

        return client
