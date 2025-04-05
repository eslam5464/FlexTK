from pathlib import Path

from lib.schemas.base import BaseSchema
from pydantic import model_validator


class TokenData(BaseSchema):
    user_id: str
    email: str
    name: str | None
    issued: float
    expires: float
    issuer: str


class FirebaseServiceAccount(BaseSchema):
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    private_key_path: Path | None = None
    client_email: str
    client_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url: str = "https://www.googleapis.com/robot/v1/metadata/x509/"
    universe_domain: str = "googleapis.com"

    @model_validator(mode="after")
    def validate_fields(self):
        self.client_x509_cert_url = self.client_x509_cert_url + self.client_email

        if self.private_key_path is not None and self.private_key_path.is_file():
            self.private_key = self.private_key_path.read_text()

        return self
