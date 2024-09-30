import io
import logging
import mimetypes
import os

import google.auth
from googleapiclient.discovery import Resource, build  # noqa
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from lib.exceptions import GoogleDriveError
from lib.schemas.google_drive import (
    DriveFile,
    DriveFileUpload,
    DriveFolder,
    DriveServiceAccount,
)

logger = logging.getLogger(__name__)


def _get_gdrive_credentials(
    service_account: DriveServiceAccount,
):
    """
    Retrieves Google Drive API credentials using a service account.
    :param service_account: The service account credentials used for authorization.
    :return: The credentials object that can be used to authenticate API requests.
    """
    creds, _ = google.auth.load_credentials_from_dict(
        info={
            "type": "service_account",
            "project_id": service_account.project_id,
            "private_key_id": service_account.private_key_id,
            "private_key": service_account.private_key.replace("\\n", "\n"),
            "client_email": service_account.client_email,
            "client_id": service_account.client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": service_account.client_x509_cert_url,
            "universe_domain": "googleapis.com",
        },
    )

    return creds


def _set_permissions(
    service: Resource,
    file_id: str,
    write_permission_email: str | None = None,
    view: bool = True,
    write: bool = False,
) -> None:
    """
    Sets permissions (viewer or writer) on a specified file in Google Drive.
    :param service: The authenticated Google Drive service resource.
    :param file_id: The ID of the file for which permissions are to be set.
    :param view: Optional. Set to True to grant reader (view-only) permission. Defaults to True.
    :param write: Optional. Set to True to grant writer (edit) permission. Defaults to False.
    :param write_permission_email: Optional. The Email to set the write permission to.
    :raises ValueError: If both view and write parameters are False.
    :raises HttpError: If an error occurs during the permissions setting process.
    """
    if write:
        if not write_permission_email:
            raise GoogleDriveError("Email must be initialized for the write permission")

        writer_permission = {
            "type": "user",
            "role": "writer",
            "emailAddress": write_permission_email,
        }
        service.permissions().create(  # noqa
            fileId=file_id,
            body=writer_permission,
            fields="id",
        ).execute()

    if view:
        viewer_permission = {"type": "anyone", "role": "reader"}
        service.permissions().create(fileId=file_id, body=viewer_permission, fields="id").execute()  # noqa


def check_folder_exists(
    folder_name: str,
    service_account: DriveServiceAccount,
) -> list[DriveFolder]:
    """
    Checks if a folder with the specified name exists in Google Drive.
    :param folder_name: The name of the folder to check.
    :param service_account: The service account credentials used for authorization.
    :return: A list of GoogleDriveFolder schemas representing matching folders.
    :raises GoogleDriveError: If an error occurs during the folder check process.
    """
    try:
        service = build(serviceName="drive", version="v3", credentials=_get_gdrive_credentials(service_account))
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' "
        results = service.files().list(q=query, spaces="drive", fields="files(id, name, parents)").execute()
        items = results.get("files", [])
        drive_folders: list[DriveFolder] = []

        if not items:
            return []

        for item in items:
            drive_folders.append(
                DriveFolder(
                    id=item["id"],
                    name=folder_name,
                    parent_ids=item["parents"],
                ),
            )

        return drive_folders
    except HttpError as error:
        logger.warning(
            msg=f"while checking folder '{folder_name}' found error: {error.reason}",
            extra={"exception": error},
        )
        raise GoogleDriveError(error.reason)


def upload_files_to_folder(
    files_to_upload: list[DriveFileUpload],
    service_account: DriveServiceAccount,
) -> list[DriveFile]:
    """
    Uploads an image file to a specified Google Drive folder. Load
    pre-authorized user credentials from the environment. For more
    information see https://developers.google.com/identity
    :param files_to_upload: List of GoogleDriveFileUpload object that contains the details of the file.
    :param service_account: The service account credentials used for authorization.
    :return: The ID of the uploaded file if successful, otherwise None.
    :raises GoogleDriveError: If an error occurs during the file upload process.
    """
    try:
        credentials = _get_gdrive_credentials(service_account)
        service = build(serviceName="drive", version="v3", credentials=credentials)
        uploaded_files: list[DriveFile] = []

        for file_entry in files_to_upload:
            file_metadata = {"name": file_entry.filename_on_drive, "parents": [file_entry.parent_folder_id]}
            file_mime_type, _ = mimetypes.guess_type(file_entry.file_path)
            media = MediaFileUpload(filename=file_entry.file_path, mimetype=file_mime_type, resumable=True)
            file_data = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            file_id = file_data.get("id")

            _set_permissions(
                file_id=file_id,
                service=service,
                view=True,
            )

            logger.info(
                msg=f"Uploaded file {os.path.basename(file_entry.file_path)} to google drive",
                extra={"file_location": file_entry.file_path},
            )

            uploaded_files.append(
                DriveFile(
                    id=file_id,
                    filename=file_entry.filename_on_drive,
                    parent_folder_id=file_entry.parent_folder_id,
                ),
            )

        return uploaded_files

    except HttpError as error:
        logger.error(msg=f"An error occurred: {error}", extra={"exception": error})
        raise GoogleDriveError(error.reason)


def create_folder(
    folder_name: str,
    service_account: DriveServiceAccount,
    parent_folder_id: str | None = None,
) -> str:
    """
    Creates a new folder in Google Drive. For more
    information see https://developers.google.com/identity
    :param folder_name: The name of the folder to be created.
    :param parent_folder_id: The ID of the Google Drive parent folder where the file will be uploaded.
    :param service_account: The service account credentials used for authorization.
    :return: The ID of the newly created folder.
    :raises GoogleDriveError: If an error occurs while creating the folder.
    """
    try:
        service = build(serviceName="drive", version="v3", credentials=_get_gdrive_credentials(service_account))
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        file_metadata_with_parent = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }
        file = (
            service.files()
            .create(body=file_metadata_with_parent if parent_folder_id else file_metadata, fields="id")
            .execute()
        )
        file_id = file.get("id")
        logger.info(f"Created folder {folder_name} in google drive with id {file_id}")

        _set_permissions(
            file_id=file_id,
            service=service,
            view=False,
            write=True,
        )

        return file_id
    except HttpError as error:
        logger.error(msg=f"An error occurred: {error.reason}", extra={"exception": error})
        raise GoogleDriveError(error.reason)


def download_file(
    file_id: str,
    save_path: str,
    service_account: DriveServiceAccount,
):
    """
    Downloads a file from Google Drive and saves it to the specified
    path. For more information see https://developers.google.com/identity
    :param file_id: The ID of the file to download from Google Drive.
    :param save_path: The local file path where the downloaded file will be saved.
    :param service_account: The service account credentials used for authorization.
    :return: The path where the file was saved.
    :raises GoogleDriveError: If an error occurs during the file download process.
    """
    try:
        service = build(serviceName="drive", version="v3", credentials=_get_gdrive_credentials(service_account))

        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        download_finished = False

        while download_finished is False:
            status, download_finished = downloader.next_chunk()
            logger.info(msg=f"Downloading file with id {file_id} at {int(status.progress() * 100)}%")

    except HttpError as error:
        logger.error(msg=f"An error occurred: {error}", extra={"exception": error})
        raise GoogleDriveError(error.reason)

    file_bytes = file.getvalue()

    with open(save_path, "wb") as outfile:
        outfile.write(file_bytes)

    return save_path


def delete_all_service_account_folders(
    service_account: DriveServiceAccount,
):
    """
    Deletes all folders owned by a specified Google Drive service account.
    :param service_account: The service account credentials used for authorization.
    :return: A list of IDs of the deleted folders if successful, otherwise an empty list.
    :raises GoogleDriveError: If any error occurs during the deletion process.
    """
    try:
        service = build(serviceName="drive", version="v3", credentials=_get_gdrive_credentials(service_account))
        query = "mimeType = 'application/vnd.google-apps.folder'"
        results = service.files().list(q=query, fields="files(id, name, parents)").execute()
        folders = results.get("files", [])

        if not folders:
            logger.info(f"No folders found when deleting all service account folders")
            return []

        deleted_folders: list[DriveFolder] = []

        for folder in folders:
            folder_id = folder["id"]
            folder_name = folder["name"]

            try:
                service.files().delete(fileId=folder_id).execute()
                logger.info(f"Deleted google drive folder {folder_name} with id {folder_id}")
                deleted_folders.append(
                    DriveFolder(id=folder_id, name=folder_name, parent_ids=folder["parents"]),
                )
            except HttpError as error:
                logger.error(
                    msg=f"Failed to delete folder: {folder_name} ({folder_id}). Error: {error.reason}",
                    extra={"exception": error},
                )
                raise GoogleDriveError(error.reason)

        return deleted_folders

    except HttpError as error:
        logger.error(
            msg=f"Error when deleting all service account folders with message: {error.reason}",
            extra={"exception": error},
        )
        raise GoogleDriveError(error.reason)
