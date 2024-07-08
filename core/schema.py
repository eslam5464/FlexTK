from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ContextKeys(StrEnum):
    config = "config"
    cloud_gcs = "gcs"
    cloud_gcs_config = "gcs_config"
    cloud_bb2 = "bb2"
    cloud_bb2_config = "bb2_config"


class ConfigKeys(StrEnum):
    hashed_password = "hashed_password"
    gcs_bucket_name = "gcs_bucket_name"
    gcs_service_account = "gcs_service_account"
    bb2_app_id = "bb2_app_id"
    bb2_app_key = "bb2_app_key"


class ClickColors(StrEnum):
    black = "black"
    red = "red"
    green = "green"
    yellow = "yellow"
    blue = "blue"
    magenta = "magenta"
    cyan = "cyan"
    white = "white"
    bright_black = "bright_black"
    bright_red = "bright_red"
    bright_green = "bright_green"
    bright_yellow = "bright_yellow"
    bright_blue = "bright_blue"
    bright_magenta = "bright_magenta"
    bright_cyan = "bright_cyan"
    bright_white = "bright_white"
    reset = "reset"


class BaseMetadata(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        strict=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )


class GCSConfiguration(BaseMetadata):
    bucket_name: str
    service_account: str


class BB2Configuration(BaseMetadata):
    app_id: str
    app_key: str
