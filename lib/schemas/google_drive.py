from .base import BaseMetadata


class GoogleDriveServiceAccount(BaseMetadata):
    private_key: str
    private_key_id: str
    project_id: str
    client_email: str
    client_id: str
    client_x509_cert_url: str


class GoogleDriveFolder(BaseMetadata):
    id: str
    name: str
    parent_ids: list[str]
