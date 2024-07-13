import os.path
import sys
from typing import Literal

import click
from core.helpers import get_bb2_configuration
from core.schema import ClickColors, ContextKeys
from lib.buckets.black_blaze_b2 import B2BucketTypeEnum, BlackBlaze
from lib.schemas.black_blaze_bucket import ApplicationData

B2_BUCKET_TYPE_VALUES = [e.value for e in B2BucketTypeEnum]


@click.group()
@click.password_option(help="Configuration password", confirmation_prompt=False)
@click.pass_context
def bb2(
    ctx: click.Context,
    password: str,
):
    """Black Blaze B2 Cloud Storage"""
    bb2_config_data = get_bb2_configuration(click_context=ctx, password=password)
    bb2_data = ApplicationData(
        app_id=bb2_config_data.app_id,
        app_key=bb2_config_data.app_key,
    )
    ctx.obj[ContextKeys.cloud_bb2_config] = bb2_config_data
    ctx.obj[ContextKeys.cloud_bb2] = BlackBlaze(bb2_data)


@click.command()
@click.option(
    "--bucket_name",
    prompt=True,
    help="Select a specific bucket",
)
@click.pass_context
def select_bucket(
    ctx: click.Context,
    bucket_name: str,
):
    """Select a bucket in Black Blaze b2"""
    black_blaze: BlackBlaze = ctx.obj[ContextKeys.cloud_bb2]
    ctx.obj[ContextKeys.cloud_bb2] = black_blaze.select_bucket(bucket_name)
    click.secho(f"Selected bucket {bucket_name}", fg=ClickColors.green)


@click.command()
@click.option(
    "--bucket_name",
    prompt=True,
    help="Select a specific bucket",
)
@click.option("--bucket_type")
@click.pass_context
def create_bucket(
    ctx: click.Context,
    bucket_name: str,
    bucket_type: Literal[B2_BUCKET_TYPE_VALUES] = B2BucketTypeEnum.all_private,  # noqa
):
    """Create a bucket in Black Blaze b2"""
    black_blaze: BlackBlaze = ctx.obj[ContextKeys.cloud_bb2]
    black_blaze.create_b2_bucket(bucket_name, bucket_type)
    click.secho(f"Created bucket {bucket_name}", fg=ClickColors.green)


@click.command()
@click.option(
    "--file_path",
    prompt=True,
    help="Path for the file on disk",
)
@click.option(
    "--bucket_path",
    prompt=True,
    help="Path for the file in the bucket",
)
@click.pass_context
def upload_file(
    ctx: click.Context,
    file_path: str,
    bucket_path: str,
):
    """Upload a file to the bucket in Black Blaze b2"""
    black_blaze: BlackBlaze = ctx.obj[ContextKeys.cloud_bb2]
    black_blaze.upload_file(local_file_path=file_path, b2_file_name=bucket_path)
    click.secho(f"Uploaded {os.path.basename(file_path)} to {bucket_path}", fg=ClickColors.green)


@click.command()
@click.option("--file_name", help="Name of the file in bucket to get its download url")
@click.option("--file_id", help="Id of the file in bucket to get its download url")
@click.pass_context
def get_download_url(
    ctx: click.Context,
    file_name: str | None = None,
    file_id: str | None = None,
):
    """Get download url for a file in the bucket"""
    if not all([file_name, file_id]):
        click.secho(
            f"Cannot get download link. One of " f"the options must have a value inorder to get the link",
            fg=ClickColors.yellow,
        )
        sys.exit()

    black_blaze: BlackBlaze = ctx.obj[ContextKeys.cloud_bb2]

    if file_id:
        download_url = black_blaze.get_download_url_by_file_id(file_id)
        click.echo("Using file id")
        click.secho(download_url, fg=ClickColors.blue)

    if file_name:
        download_url = black_blaze.get_download_url_by_name(file_name)
        click.echo("Using file name")
        click.secho(download_url, fg=ClickColors.blue)


@click.command()
@click.option("--file_name", help="Name of the file in bucket to delete")
@click.option("--file_id", help="Id of the file in bucket to delete")
@click.pass_context
def delete_file(
    ctx: click.Context,
    file_id: str | None = None,
    file_name: str | None = None,
):
    """Delete a file in the bucket"""
    if not all([file_name, file_id]):
        click.secho(
            f"Cannot delete the file. One of " f"the options must have a value inorder to get the link",
            fg=ClickColors.yellow,
        )
        sys.exit()

    black_blaze: BlackBlaze = ctx.obj[ContextKeys.cloud_bb2]
    black_blaze.delete_file(file_id, file_name)
    click.secho(f"File deleted", fg=ClickColors.green)


bb2.add_command(select_bucket)
bb2.add_command(create_bucket)
bb2.add_command(upload_file)
bb2.add_command(get_download_url)
bb2.add_command(delete_file)
