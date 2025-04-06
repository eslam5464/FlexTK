from enum import StrEnum
from typing import Any

from requests.structures import CaseInsensitiveDict

from .base import BaseSchema


class HTTPRequestMethod(StrEnum):
    connect = "CONNECT"
    delete = "DELETE"
    get = "GET"
    head = "HEAD"
    options = "OPTIONS"
    patch = "PATCH"
    post = "POST"
    put = "PUT"
    trace = "TRACE"


class ApiResponse(BaseSchema):
    status_code: int
    message: str
    json_data: dict
    text_data: str
    reason: str
    headers: CaseInsensitiveDict
    raw: Any
    extra: Any | None = None
