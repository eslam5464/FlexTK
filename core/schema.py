from enum import StrEnum


class ContextKeys(StrEnum):
    config = "config"


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
