import os

import click
from core.helpers import get_gcs_configuration
from core.schema import ClickColors, ContextKeys
from lib.storage.buckets.gcs import GCS


@click.group()
@click.password_option(help="Configuration password", confirmation_prompt=False)
@click.pass_context
def gcs(
    ctx: click.Context,
    password: str,
):
    """Google Cloud Storage"""
    gcs_config = get_gcs_configuration(click_context=ctx, password=password)
    ctx.obj[ContextKeys.cloud_gcs_config] = gcs_config
    ctx.obj[ContextKeys.cloud_gcs] = GCS(gcs_config.bucket_name, gcs_config.service_account)


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
    """Select a bucket in Google Cloud Storage"""
    google_cloud_service: GCS = ctx.obj[ContextKeys.cloud_gcs]
    google_cloud_service = google_cloud_service.set_bucket(bucket_name)
    ctx.obj[ContextKeys.cloud_gcs] = google_cloud_service
    click.secho(f"Selected bucket '{bucket_name}'", fg=ClickColors.green)


@click.command()
@click.option(
    "--file_path",
    prompt=True,
    help="File location on disk",
)
@click.option(
    "--bucket_path",
    prompt=True,
    help="Path to be uploaded into bucket",
)
@click.pass_context
def upload_file(
    ctx: click.Context,
    file_path: str,
    bucket_path: str,
):
    """Upload a file to the specified bucket place"""
    google_cloud_service: GCS = ctx.obj[ContextKeys.cloud_gcs]
    google_cloud_service.upload_file(file_path=file_path, bucket_folder_path=bucket_path)
    click.secho(f"Uploaded {os.path.basename(file_path)} to {bucket_path}", fg=ClickColors.green)


@click.command()
@click.option(
    "--bucket_path",
    prompt=True,
    help="Path of the bucket folder to get all of the files in it",
)
@click.pass_context
def get_files(
    ctx: click.Context,
    bucket_path: str,
):
    """list files in the specified bucket path"""
    get_gcs_configuration(click_context=ctx)
    google_cloud_service: GCS = ctx.obj[ContextKeys.cloud_gcs]
    files_in_bucket_path = google_cloud_service.get_files(bucket_path)

    for index, file_entry in enumerate(files_in_bucket_path, start=1):
        click.secho(f"{index}- {file_entry}", fg=ClickColors.bright_blue)


@click.command()
@click.option(
    "--folder_name",
    prompt=True,
    help="Full path of the folder in the bucket",
)
@click.pass_context
def create_folder(
    ctx: click.Context,
    folder_name: str,
):
    """Create a folder in the specified bucket path"""
    google_cloud_service: GCS = ctx.obj[ContextKeys.cloud_gcs]
    google_cloud_service.create_folder(folder_name)
    click.secho(f"Created bucket folder '{folder_name}'", fg=ClickColors.green)


@click.command()
@click.option(
    "--file_path",
    prompt=True,
    help="Path of the file in the bucket to be deleted",
)
@click.pass_context
def delete_file(
    ctx: click.Context,
    file_path: str,
):
    """Delete the file in the specified bucket path"""
    google_cloud_service: GCS = ctx.obj[ContextKeys.cloud_gcs]
    google_cloud_service.delete_files([file_path])
    click.secho(f"Deleted file {file_path}", fg=ClickColors.green)


gcs.add_command(get_files)
gcs.add_command(upload_file)
gcs.add_command(select_bucket)
gcs.add_command(create_folder)
gcs.add_command(delete_file)
