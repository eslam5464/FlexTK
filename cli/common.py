import sys
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


def get_config_password(click_context: click.Context) -> str:
    """
    Retrieves the configuration password from the Click context.
    :param click_context: The Click context containing the configuration data.
    :return: The hashed password from the configuration.
    :raises SystemExit: If the password is not set in the configuration.
    """
    config_data: dict[str, Any] = click_context.obj[ContextKeys.config]
    current_pass = config_data.get(ConfigKeys.hashed_password)

    if current_pass is None:
        click.secho("Password is not set to perform this operation", fg=ClickColors.red)
        sys.exit()

    return current_pass


def get_gcs_configuration(click_context: click.Context) -> GCSConfiguration:
    """
    Retrieves and decrypts the GCS configuration settings.
    :param click_context: The Click context containing the configuration data.
    :return: An instance of GCSConfiguration with decrypted settings.
    :raises SystemExit: If the configuration is not set properly or the password is incorrect.
    """
    config_password = get_config_password(click_context=click_context)
    fernet = Fernet(config_password.encode())
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
