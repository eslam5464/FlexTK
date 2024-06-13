from b2sdk.v2.exception import NonExistentBucket
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


class B2BucketNotFoundError(BlackBlazeError):
    """
    Bucket does not exist in black blaze
    """

    def __init__(self, message, exception: NonExistentBucket | None = NonExistentBucket):
        super().__init__(message, exception)


class B2BucketNotSelectedError(BlackBlazeError):
    """
    Bucket is not selected
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

    def __init__(self, message, exception: NotFound | None = NotFound):
        super().__init__(message, exception)


class GCSBucketNotSelectedError(GCSError):
    """
    Bucket is not selected
    """

    def __init__(self, message, exception: Exception | None = None):
        super().__init__(message, exception)
