import os.path
import sys
from base64 import urlsafe_b64encode
from typing import Any

import click
from core.config import save_config
from core.helpers import validate_password
from core.schema import ClickColors, ConfigKeys, ContextKeys
from cryptography.fernet import Fernet
from lib.utils.misc import generate_random_password


@click.command()
@click.password_option(help="Password to set for configuration")
@click.pass_context
def set_password(
    ctx: click.Context,
    password: str,
):
    """Set the password for configurations and secret keys with the removal of all previous configurations"""
    if len(password) > 32:
        click.secho("Can't set the password with length more than 32 letters", fg=ClickColors.red)
        sys.exit()

    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    current_match_password = config_data.get(ConfigKeys.match_password)

    if current_match_password is not None:
        click.secho("Can't set password because it has already been set", fg=ClickColors.yellow)
        sys.exit()

    password = password.zfill(32)
    key = urlsafe_b64encode(password.encode())
    new_match_password_encoded = generate_random_password(32).encode()
    fernet = Fernet(key)
    match_password_encrypted = fernet.encrypt(new_match_password_encoded).decode()
    save_config({ConfigKeys.match_password: match_password_encrypted})
    click.secho("Password has been set", fg=ClickColors.green)


@click.command()
@click.password_option(help="New password to reset the old one")
@click.pass_context
def reset_password(
    ctx: click.Context,
    password: str,
):
    """Reset the current password with the removal of all configurations"""
    if len(password) > 32:
        click.secho("Can't set the password with length more than 32 letters", fg=ClickColors.red)
        sys.exit()

    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    current_match_password = config_data.get(ConfigKeys.match_password)

    if current_match_password is not None:
        click.secho("Can't set password because it has already been set", fg=ClickColors.yellow)
        sys.exit()

    password = password.zfill(32)
    key = urlsafe_b64encode(password.encode())
    match_password = generate_random_password(32)
    fernet = Fernet(key)
    match_password_encrypted = fernet.encrypt(match_password.encode()).decode()
    save_config({ConfigKeys.match_password: match_password_encrypted})
    click.secho("Password is changed and all configurations are removed", fg=ClickColors.green)


@click.command()
@click.password_option(help="Configuration password", confirmation_prompt=False)
@click.option("--bucket_name", prompt=True, help="Default bucket name for GCS to be selected")
@click.option("--service_account", prompt=True, help="Path for JSON file for GCS service account")
@click.pass_context
def gcs(
    ctx: click.Context,
    bucket_name: str,
    service_account: str,
    password: str,
):
    """Configure google cloud storage"""
    if not os.path.exists(service_account):
        click.secho("Service account file does not exist", fg=ClickColors.red)
        sys.exit()

    if not service_account.lower().endswith(".json"):
        click.secho("Service account is not a json file", fg=ClickColors.red)
        sys.exit()

    password_b64_encoded = validate_password(password=password, click_context=ctx)
    fernet = Fernet(password_b64_encoded)
    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    config_data[ConfigKeys.gcs_bucket_name] = fernet.encrypt(bucket_name.encode()).decode()
    config_data[ConfigKeys.gcs_service_account] = fernet.encrypt(service_account.encode()).decode()
    save_config(config_data)
    click.secho("GCS configuration is set", fg=ClickColors.green)


@click.command()
@click.password_option(help="Configuration password", confirmation_prompt=False)
@click.option("--app_id", prompt=True, help="Black blaze application id")
@click.option("--app_key", prompt=True, help="Black blaze application key")
@click.pass_context
def bb2(
    ctx: click.Context,
    app_id: str,
    app_key: str,
    password: str,
):
    """Configure Black Blaze B2 storage"""
    password_b64_encoded = validate_password(password=password, click_context=ctx)
    fernet = Fernet(password_b64_encoded)
    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    config_data[ConfigKeys.bb2_app_id] = fernet.encrypt(app_id.encode()).decode()
    config_data[ConfigKeys.bb2_app_key] = fernet.encrypt(app_key.encode()).decode()
    save_config(config_data)
    click.secho("Black Blaze configuration is set", fg=ClickColors.green)


@click.command()
@click.password_option(help="Configuration password", confirmation_prompt=False)
@click.option("--app_id", prompt=True, help="Unsplash application id")
@click.option("--access_key", prompt=True, help="Unsplash access key")
@click.option("--secret_key", prompt=True, help="Unsplash secret key")
@click.pass_context
def unsplash(
    ctx: click.Context,
    app_id: str,
    access_key: str,
    secret_key: str,
    password: str,
):
    """Configuration for unsplash to download images"""
    password_b64_encoded = validate_password(password=password, click_context=ctx)
    fernet = Fernet(password_b64_encoded)
    config_data: dict[str, Any] = ctx.obj[ContextKeys.config]
    config_data[ConfigKeys.unsplash_app_id] = fernet.encrypt(app_id.encode()).decode()
    config_data[ConfigKeys.unsplash_access_key] = fernet.encrypt(access_key.encode()).decode()
    config_data[ConfigKeys.unsplash_secret_key] = fernet.encrypt(secret_key.encode()).decode()
    save_config(config_data)
    click.secho("Unsplash configuration is set", fg=ClickColors.green)
