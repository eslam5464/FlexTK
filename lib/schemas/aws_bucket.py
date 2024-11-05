from datetime import datetime

from .base import BaseSchema


class AccessData(BaseSchema):
    access_key: str
    secret_key: str


class BucketData(BaseSchema):
    bucket_name: str
    region_name: str


class BucketFile(BaseSchema):
    id: str
    basename: str
    extension: str
    file_path_in_bucket: str
    bucket_name: str
    public_url: str
    size_bytes: int
    modification_date: datetime
    content_type: str
