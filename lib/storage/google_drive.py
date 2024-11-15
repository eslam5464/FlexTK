import io
import logging
import mimetypes
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from lib.exceptions import GoogleDriveError
from lib.schemas.google_drive import (
    DriveBlobPermissions,
    DriveCredentials,
    DriveFile,
    DriveFileDownload,
    DriveFileUpload,
    DriveFolder,
)
from pydantic import EmailStr

logger = logging.getLogger(__name__)


@dataclass(init=False)
class GoogleDrive:
    __token_path: Path | None = field(default=None)
    __credentials: Credentials | None = field(default=None)
    __drive_credentials: DriveCredentials | None = field(default=None)

    def __init__(
        self,
        drive_credentials: DriveCredentials | str,
        token_path: Path | None = None,
        retrieve_new_token: bool = False,
    ):
        """
        Initializes a new instance of the GoogleDrive class, allowing interaction with the Google Drive API.
        :param drive_credentials: An instance of DriveCredentials or the path for the credentials JSON path.
        :param token_path: Optional. A Path object specifying where the token file is stored on disk.

        This class utilizes the Google Drive API to perform operations such as file uploads,
        downloads, folder management, and more. It requires authentication via OAuth 2.0.
        For more information about setting up and using the Google Drive API,
        refer to the Google Drive API Quickstart documentation:
        https://developers.google.com/drive/api/quickstart/python
        """
        if token_path:
            self.__token_path = Path(token_path)
        else:
            self.__token_path = Path.home() / ".config" / "my_google_drive" / "google_drive_token.json"

        if retrieve_new_token and self.__token_path.exists():
            os.remove(self.__token_path)

        if isinstance(drive_credentials, str):
            if not os.path.isfile(drive_credentials):
                raise FileNotFoundError("Google drive JSON file not found")
            if not drive_credentials.lower().endswith(".json"):
                _, file_extension = os.path.splitext(drive_credentials.lower())
                raise ValueError(f"Google Drive credentials is not a json file: {file_extension}")

        self.__drive_credentials = drive_credentials
        self.__credentials = self._get_gdrive_credentials()
        self.__service = self._get_service()

    @property
    def token_path(self) -> str:
        """
        Retrieves the path for the access token path on disk.
        :return: The path for the access token
        """
        return str(self.__token_path)

    def get_files(self, parent_folder_id: str) -> list[DriveFile]:
        """
        Retrieves all files from a specified Google Drive folder that are not in the trash.
        :param parent_folder_id: The ID of the parent folder to retrieve files from.
        :return: A list of DriveFile objects representing the files in the folder.
        """
        files_in_folder = []
        query = f"'{parent_folder_id}' in parents and trashed=false"
        request_fields = "files(id, name, mimeType, size, parents, shared, trashed, createdTime, thumbnailLink, "
        request_fields += "modifiedTime, version, originalFilename, trashedTime, fileExtension, owners, permissions)"
        request = self.__service.files().list(q=query, fields=request_fields).execute()

        for file_entry in request.get("files"):
            thumbnail: str = file_entry.get("thumbnailLink")
            thumbnail_large = None if not thumbnail else thumbnail.split("=")[0]

            files_in_folder.append(
                DriveFile(
                    id=file_entry.get("id"),
                    filename=file_entry.get("name"),
                    in_trash=file_entry.get("trashed"),
                    creation_timestamp=file_entry.get("createdTime"),
                    modification_timestamp=file_entry.get("modifiedTime"),
                    extension=file_entry.get("fileExtension"),
                    size_bytes=file_entry.get("size"),
                    version=file_entry.get("version"),
                    is_shared=file_entry.get("shared"),
                    mimeType=file_entry.get("mimeType"),
                    original_filename=file_entry.get("originalFilename"),
                    parent_folder_ids=file_entry.get("parents"),
                    thumbnail_url=thumbnail,
                    thumbnail_large_url=thumbnail_large,
                    owners=file_entry.get("owners"),
                    permissions=file_entry.get("permissions"),
                ),
            )

        return files_in_folder

    def get_file(self, file_id: str) -> DriveFile:
        """
        Retrieves metadata for a file from Google Drive using its file ID.
        :param file_id: The ID of the file to retrieve.
        :return: A DriveFile object containing file metadata or None if no file is found.
        :raises GoogleDriveError: If an error occurs during the API request.
        """
        try:
            request_fields = "id, name, mimeType, size, parents, shared, trashed, createdTime, thumbnailLink, "
            request_fields += "modifiedTime, version, originalFilename, trashedTime, fileExtension, owners, permissions"
            request = (
                self.__service.files()
                .get(
                    fileId=file_id,
                    fields=request_fields,
                )
                .execute()
            )
            thumbnail: str = request.get("thumbnailLink")
            thumbnail_large = None if not thumbnail else thumbnail.split("=")[0]

            return DriveFile(
                id=request.get("id"),
                filename=request.get("name"),
                in_trash=request.get("trashed"),
                creation_timestamp=request.get("createdTime"),
                modification_timestamp=request.get("modifiedTime"),
                extension=request.get("fileExtension"),
                size_bytes=request.get("size"),
                version=request.get("version"),
                is_shared=request.get("shared"),
                mimeType=request.get("mimeType"),
                original_filename=request.get("originalFilename"),
                parent_folder_ids=request.get("parents"),
                thumbnail_url=thumbnail,
                thumbnail_large_url=thumbnail_large,
                owners=request.get("owners"),
                permissions=request.get("permissions"),
            )
        except HttpError as error:
            logger.error(
                msg=f"while retrieving file with id '{file_id}' found error: {error.reason}",
                extra={"exception": error},
            )
            raise GoogleDriveError(error.reason)

    def check_folder_exists(
        self,
        folder_name: str,
    ) -> list[DriveFolder]:
        """
        Checks if a folder with the specified name exists in Google Drive.
        :param folder_name: The name of the folder to check.
        :return: A list of GoogleDriveFolder schemas representing matching folders.
        :raises GoogleDriveError: If an error occurs during the folder check process.
        """
        drive_folders: list[DriveFolder] = []

        try:
            query = f"name contains '{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
            results = (
                self.__service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="files(id, name, parents, trashed)",
                )
                .execute()
            )
            all_items = results.get("files", [])

            if not all_items:
                return []

            for item_entry in all_items:
                drive_folders.append(
                    DriveFolder(
                        id=item_entry.get("id"),
                        name=folder_name,
                        parent_ids=item_entry.get("parents"),
                        in_trash=item_entry.get("trashed"),
                    ),
                )

            return drive_folders
        except HttpError as error:
            logger.error(
                msg=f"while checking folder '{folder_name}' found error: {error.reason}",
                extra={"exception": error},
            )
            raise GoogleDriveError(error.reason)

    def upload_files(
        self,
        files_to_upload: list[DriveFileUpload],
    ) -> list[DriveFile]:
        """
        Uploads an image file to a specified Google Drive folder. Load
        pre-authorized user credentials from the environment. For more
        information see https://developers.google.com/identity
        :param files_to_upload: List of GoogleDriveFileUpload object that contains the details of the file.
        :return: The ID of the uploaded file if successful, otherwise None.
        :raises GoogleDriveError: If an error occurs during the file upload process.
        """
        try:
            uploaded_files: list[DriveFile] = []

            for file_entry in files_to_upload:
                file_metadata = {"name": file_entry.filename_on_drive, "parents": [file_entry.parent_folder_id]}
                file_mime_type, _ = mimetypes.guess_type(file_entry.file_path)
                media = MediaFileUpload(filename=file_entry.file_path, mimetype=file_mime_type, resumable=True)
                file_data = self.__service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                file_id = file_data.get("id")

                self._set_permissions(
                    file_id=file_id,
                    public_view=file_entry.permissions.public_read,
                    write_permission_email=file_entry.permissions.writer_email,
                    read_permission_email=file_entry.permissions.reader_email,
                )

                logger.info(
                    msg=f"Uploaded file {os.path.basename(file_entry.file_path)} to google drive",
                    extra={"file_location": file_entry.file_path},
                )
                uploaded_files.append(self.get_file(file_id))

            return uploaded_files
        except HttpError as error:
            logger.error(msg=f"An error occurred: {error}", extra={"exception": error})
            raise GoogleDriveError(error.reason)

    def create_folder(
        self,
        folder_name: str,
        permissions: DriveBlobPermissions,
        parent_folder_id: str | None = None,
    ) -> DriveFolder:
        """
        Creates a new folder in Google Drive. For more
        information see https://developers.google.com/identity
        :param folder_name: The name of the folder to be created.
        :param parent_folder_id: The ID of the Google Drive parent folder where the file will be uploaded.
        :param permissions: An instance of DriveBlobPermissions that defines the access control for the folder.
        :return: The ID of the newly created folder.
        :raises GoogleDriveError: If an error occurs while creating the folder.
        """
        try:
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            file_metadata_with_parent = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_folder_id],
            }
            folder_data = (
                self.__service.files()
                .create(body=file_metadata_with_parent if parent_folder_id else file_metadata, fields="id")
                .execute()
            )
            folder_id = folder_data.get("id")
            logger.info(f"Created folder {folder_name} in google drive with id {folder_id}")

            self._set_permissions(
                file_id=folder_id,
                public_view=permissions.public_read,
                write_permission_email=permissions.writer_email,
                read_permission_email=permissions.reader_email,
            )

            return DriveFolder(
                id=folder_id,
                name=folder_name,
                parent_ids=[] if not parent_folder_id else [parent_folder_id],
                in_trash=False,
            )
        except HttpError as error:
            logger.error(msg=f"An error occurred: {error.reason}", extra={"exception": error})
            raise GoogleDriveError(error.reason)

    def download_files(
        self,
        files_data: list[DriveFileDownload],
    ) -> Self:
        """
        Download files from Google Drive and saves it to the specified
        path. For more information see https://developers.google.com/identity
        :param files_data: List of DriveFileDownload object contains files data.
        :return: The path where the file was saved.
        :raises GoogleDriveError: If an error occurs during the file download process.
        """
        try:
            for file_entry in files_data:
                current_file = self.get_file(file_entry.file_id)

                request = self.__service.files().get_media(fileId=current_file.id)
                file = io.BytesIO()
                downloader = MediaIoBaseDownload(file, request)
                download_finished = False

                while download_finished is False:
                    status, download_finished = downloader.next_chunk()
                    logger.info(msg=f"Downloading file with id {current_file.id} at {status.progress() * 100:.2f}%")

                file_bytes = file.getvalue()
                file_full_path = os.path.join(file_entry.save_path, current_file.filename)

                with open(file_full_path, "wb") as outfile:
                    outfile.write(file_bytes)
        except HttpError as error:
            logger.error(msg=f"An error occurred: {error}", extra={"exception": error})
            raise GoogleDriveError(error.reason)

        return self

    def _set_permissions(
        self,
        file_id: str,
        write_permission_email: EmailStr | None = None,
        read_permission_email: EmailStr | None = None,
        public_view: bool = False,
    ) -> None:
        """
        Sets permissions (viewer or writer) on a specified file in Google Drive.
        :param file_id: The ID of the file for which permissions are to be set.
        :param public_view: Optional. Set to True to grant public reader (view-only) permission. Defaults to True.
        :param write_permission_email: Optional. The Email to set the write permission to.
        :param read_permission_email: Optional. The Email to set the read permission to.
        :raises ValueError: If both view and write parameters are False.
        :raises HttpError: If an error occurs during the permissions setting process.
        """
        if write_permission_email:
            writer_permission = {
                "type": "user",
                "role": "writer",
                "emailAddress": write_permission_email,
            }
            self.__service.permissions().create(  # noqa
                fileId=file_id,
                body=writer_permission,
                fields="id",
            ).execute()

        if read_permission_email:
            reader_permission = {
                "type": "user",
                "role": "reader",
                "emailAddress": read_permission_email,
            }
            self.__service.permissions().create(  # noqa
                fileId=file_id,
                body=reader_permission,
                fields="id",
            ).execute()

        if public_view:
            viewer_permission = {"type": "anyone", "role": "reader"}
            self.__service.permissions().create(fileId=file_id, body=viewer_permission, fields="id").execute()  # noqa

    def _get_gdrive_credentials(
        self,
    ) -> Credentials:
        """
        Retrieves Google Drive API credentials using a service account.
        :return: The credentials object that can be used to authenticate API requests.
        """
        scopes = self.__drive_credentials.scopes if isinstance(self.__drive_credentials, DriveCredentials) else None
        credentials = None

        if scopes is None:
            scopes = ["https://www.googleapis.com/auth/drive"]

        if os.path.exists(self.__token_path):
            logger.info(msg="Found google drive token on disk", extra={"file_location": str(self.__token_path)})
            credentials = Credentials.from_authorized_user_file(filename=str(self.__token_path), scopes=scopes)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                logger.info(msg="Google drive token expired, getting a new token by refreshing it")

                try:
                    credentials.refresh(Request())
                except RefreshError as err:
                    logger.error(
                        msg="Error while refreshing credentials. Token will be deleted",
                        extra={"exception": str(err)},
                    )

                    if os.path.isfile(self.__token_path):
                        os.remove(self.__token_path)
                        logger.debug(
                            msg="Deleted the token in path",
                            extra={"file_path": self.__token_path},
                        )
                    else:
                        logger.debug(
                            msg="Could not delete the token in path",
                            extra={"file_path": self.__token_path},
                        )

                    raise GoogleDriveError(
                        "Error while refreshing credentials. Token will be deleted, please re-run the command",
                    )
            else:
                logger.info(msg="Google drive is valid, creating the credentials from the token")

                if isinstance(self.__drive_credentials, str):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        client_secrets_file=self.__drive_credentials,
                        scopes=scopes,
                    )
                elif isinstance(self.__drive_credentials, DriveCredentials):
                    flow = InstalledAppFlow.from_client_config(
                        client_config=self.__drive_credentials.model_dump(exclude={"scopes"}),
                        scopes=scopes,
                    )
                else:
                    raise GoogleDriveError(f"Unsupported type of credentials: {type(self.__drive_credentials)}")

                credentials = flow.run_local_server(port=0, timeout_seconds=300)

            if not self.__token_path.parent.exists():
                self.__token_path.parent.mkdir()

            with open(self.__token_path, "w") as token:
                logger.info(
                    msg="Writing the google drive token on disk",
                    extra={"file_location": str(self.__token_path)},
                )
                token.write(credentials.to_json())

        return credentials

    def _get_service(self):
        """
        Retrieves the Google Drive service using the provided service account credentials.
        :return: Google Drive service object.
        :raises: Exception if the service creation fails.
        """
        service = build(serviceName="drive", version="v3", credentials=self.__credentials, cache_discovery=False)

        return service

    def _delete_all_service_account_folders(self):
        """
        Deletes all folders owned by a specified Google Drive service account.
        :return: A list of IDs of the deleted folders if successful, otherwise an empty list.
        :raises GoogleDriveError: If any error occurs during the deletion process.
        """
        try:
            query = "mimeType = 'application/vnd.google-apps.folder'"
            results = self.__service.files().list(q=query, fields="files(id, name, parents)").execute()
            folders = results.get("files", [])

            if not folders:
                logger.info(f"No folders found when deleting all service account folders")
                return []

            deleted_folders: list[DriveFolder] = []

            for folder in folders:
                folder_id = folder["id"]
                folder_name = folder["name"]

                try:
                    self.__service.files().delete(fileId=folder_id).execute()
                    logger.info(f"Deleted google drive folder {folder_name} with id {folder_id}")
                    deleted_folders.append(
                        DriveFolder(id=folder_id, name=folder_name, parent_ids=folder["parents"], in_trash=True),
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
