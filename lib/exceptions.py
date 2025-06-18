from b2sdk.v2.exception import NonExistentBucket
from botocore.exceptions import ClientError, NoCredentialsError
from google.api_core.exceptions import NotFound


class CustomException(Exception):
    """
    Base for all custom exceptions
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.exception = exception

    def __str__(self):
        if self.exception:
            return f"{self.message}\nException: {self.exception}"

        return self.message


class BlackBlazeError(CustomException):
    """
    Base exception for black blaze b2
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class B2BucketOperationError(BlackBlazeError):
    """
    Bucket operation error for black blaze b2
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class B2BucketNotFoundError(BlackBlazeError):
    """
    Bucket does not exist in black blaze
    """

    def __init__(
        self,
        message,
        exception: NonExistentBucket | None = None,
    ):
        super().__init__(message, exception)


class B2BucketNotSelectedError(BlackBlazeError):
    """
    Bucket is not selected
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class B2AuthorizationError(BlackBlazeError):
    """
    Authorization error for black blaze b2
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class B2FileOperationError(BlackBlazeError):
    """
    File operation error for black blaze b2
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class GCSError(CustomException):
    """
    Base exception for Google cloud service
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class GCSBucketNotFoundError(GCSError):
    """
    Bucket does not exist in Google cloud service
    """

    def __init__(self, message, exception: NotFound | None = None):
        super().__init__(message, exception)


class GCSBucketNotSelectedError(GCSError):
    """
    Bucket is not selected
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class GoogleDriveError(CustomException):
    """
    Base exception for Google Drive
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class AWSError(CustomException):
    """
    Base exception for AWS
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)


class AWSNoCredentialsError(AWSError):
    """
    No Credentials
    """

    def __init__(self, message, exception: NoCredentialsError | None = None):
        super().__init__(message, exception)


class AWSBucketNotFoundError(AWSError):
    """
    Bucket does not exist in AWS
    """

    def __init__(self, message, exception: ClientError | None = None):
        super().__init__(message, exception)
