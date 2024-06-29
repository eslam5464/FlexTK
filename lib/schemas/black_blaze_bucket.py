from lib.schemas.base import BaseMetadata


class ApplicationData(BaseMetadata):
    app_id: str
    app_key: str


class FileDownloadLink(BaseMetadata):
    download_url: str
    auth_token: str | None
