import sys
from base64 import urlsafe_b64encode
from typing import Any

import click
from core.schema import (
    BB2Configuration,
    ClickColors,
    ConfigKeys,
    ContextKeys,
    GCSConfiguration,
)
from cryptography.fernet import Fernet, InvalidToken


def get_match_password(click_context: click.Context) -> str:
    """
    Retrieves the match password from the Click context.
    :param click_context: The Click context object that holds the configuration data.
    :return: The current match password as a string.
    :raises SystemExit: If the match password is not set.
    """
    config_data: dict[str, Any] = click_context.obj[ContextKeys.config]
    current_match_password = config_data.get(ConfigKeys.match_password)

    if current_match_password is None:
        click.secho("Password is not set to perform this operation", fg=ClickColors.red)
        sys.exit()

    return current_match_password


def validate_password(password: str, click_context: click.Context) -> bytes:
    """
    Validates the provided password and returns the base64 encoded version if valid.
    :param password: The password to validate.
    :param click_context: The Click context object that holds the configuration data.
    :return: The base64 encoded version of the validated password.
    :raises SystemExit: If the password length is more than 32 characters or if the password is invalid.
    """
    if len(password) > 32:
        click.secho("The password has length more than 32 letters", fg=ClickColors.red)
        sys.exit()

    match_password = get_match_password(click_context=click_context)
    password_b64_encoded = urlsafe_b64encode(password.zfill(32).encode())
    fernet = Fernet(password_b64_encoded)

    try:
        fernet.decrypt(match_password).decode()
    except InvalidToken as ex:
        click.secho("Invalid password", fg=ClickColors.red)
        sys.exit()

    return password_b64_encoded


def get_gcs_configuration(click_context: click.Context, password: str) -> GCSConfiguration:
    """
    Retrieves and decrypts the GCS configuration settings.
    :param click_context: The Click context containing the configuration data.
    :param password: The password to decrypt the configuration data.
    :return: An instance of GCSConfiguration with decrypted settings.
    :raises SystemExit: If the configuration is not set properly or the password is incorrect.
    """
    password_b64_encoded = validate_password(password=password, click_context=click_context)
    fernet = Fernet(password_b64_encoded)
    config_data: dict[str, Any] = click_context.obj[ContextKeys.config]
    config_gcs_bucket_name = config_data.get(ConfigKeys.gcs_bucket_name)
    config_gcs_service_account = config_data.get(ConfigKeys.gcs_service_account)

    if not all([config_gcs_bucket_name, config_gcs_service_account]):
        click.secho("GCS not configured properly. Please reconfigure.", fg=ClickColors.red)
        sys.exit()

    try:
        gcs_bucket_name = fernet.decrypt(config_gcs_bucket_name).decode()
        gcs_service_account = fernet.decrypt(config_gcs_service_account).decode()
    except InvalidToken as ex:
        click.secho("Wrong password for configuration", fg=ClickColors.red)
        sys.exit()

    return GCSConfiguration(
        bucket_name=gcs_bucket_name,
        service_account=gcs_service_account,
    )


def get_bb2_configuration(click_context: click.Context, password: str) -> BB2Configuration:
    """
    Retrieves and decrypts the BB2 configuration settings.
    :param click_context: The Click context containing the configuration data.
    :param password: The password to decrypt the configuration data.
    :return: An instance of BB2Configuration with decrypted settings.
    :raises SystemExit: If the configuration is not set properly or the password is incorrect.
    """
    password_b64_encoded = validate_password(password=password, click_context=click_context)
    fernet = Fernet(password_b64_encoded)
    config_data: dict[str, Any] = click_context.obj[ContextKeys.config]
    config_bb2_app_id = config_data.get(ConfigKeys.bb2_app_id)
    config_bb2_app_key = config_data.get(ConfigKeys.bb2_app_key)

    if not all([config_bb2_app_id, config_bb2_app_key]):
        click.secho("Black Blaze not configured properly. Please reconfigure.", fg=ClickColors.red)
        sys.exit()

    try:
        bb2_app_id = fernet.decrypt(config_bb2_app_id).decode()
        bb2_app_key = fernet.decrypt(config_bb2_app_key).decode()
    except InvalidToken as ex:
        click.secho("Wrong password for configuration", fg=ClickColors.red)
        sys.exit()

    return BB2Configuration(
        app_id=bb2_app_id,
        app_key=bb2_app_key,
    )
