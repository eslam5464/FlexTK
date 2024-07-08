import os.path
import sys
from base64 import urlsafe_b64encode
from typing import Any

import click
from cli.common import get_config_password
from core.config import save_config
from core.schema import ClickColors, ConfigKeys, ContextKeys
from cryptography.fernet import Fernet


@click.command()
@click.option(
    "--pass_key",
    prompt=True,
    hide_input=True,
    help="Password to set for configuration",
)
@click.pass_context
def set_password(
    ctx: click.Context,
    pass_key: str,
):
    """Set the password for configurations and secret keys with the removal of all previous configurations"""
    if len(pass_key) <= 32:
        pass_key = pass_key.zfill(32)
    elif len(pass_key) > 32:
        click.secho("Can't set the password with length more than 32 letters", fg=ClickColors.red)

    key = urlsafe_b64encode(pass_key.encode())
    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    current_pass = config_data.get(ConfigKeys.hashed_password)

    if current_pass is None:
        save_config({ConfigKeys.hashed_password: key.decode()})
        click.secho("Password has been set", fg=ClickColors.green)
        return

    click.secho("Can't set password because it has already been set", fg=ClickColors.yellow)


@click.command()
@click.option(
    "--pass_key",
    prompt=True,
    hide_input=True,
    help="New password to reset the old one",
)
@click.pass_context
def reset_password(
    pass_key: str,
):
    """Reset the current password with the removal of all configurations"""
    if len(pass_key) <= 32:
        pass_key = pass_key.zfill(32)
    elif len(pass_key) > 32:
        click.secho("Can't set the password with length more than 32 letters", fg=ClickColors.red)

    key = urlsafe_b64encode(pass_key.encode())
    save_config({ConfigKeys.hashed_password: key.decode()})
    click.secho("Password is changed and all configurations are removed", fg=ClickColors.green)


@click.command()
@click.option("--bucket_name", prompt=True, help="Default bucket name for GCS to be selected")
@click.option("--service_account", prompt=True, help="Path for JSON file for GCS service account")
@click.pass_context
def gcs(
    ctx: click.Context,
    bucket_name: str,
    service_account: str,
):
    """Configure google cloud storage"""
    if os.path.exists(service_account):
        click.secho("Service account file does not exist", fg=ClickColors.red)
        sys.exit()

    if not service_account.lower().endswith(".json"):
        click.secho("Service account is not a json file", fg=ClickColors.red)
        sys.exit()

    config_password = get_config_password(click_context=ctx)
    fernet = Fernet(config_password.encode())
    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    config_data[ConfigKeys.gcs_bucket_name] = fernet.encrypt(bucket_name.encode()).decode()
    config_data[ConfigKeys.gcs_service_account] = fernet.encrypt(service_account.encode()).decode()
    save_config(config_data)
    click.secho("GCS configuration is set", fg=ClickColors.green)


@click.command()
@click.option("--app_id", prompt=True, help="Black blaze application id")
@click.option("--app_key", prompt=True, help="Black blaze application key")
@click.pass_context
def bb2(
    ctx: click.Context,
    app_id: str,
    app_key: str,
):
    """Configure Black Blaze B2 storage"""
    config_password = get_config_password(click_context=ctx)
    fernet = Fernet(config_password.encode())
    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    config_data[ConfigKeys.bb2_app_id] = fernet.encrypt(app_id.encode()).decode()
    config_data[ConfigKeys.bb2_app_key] = fernet.encrypt(app_key.encode()).decode()
    save_config(config_data)
    click.secho("Black Blaze configuration is set", fg=ClickColors.green)
