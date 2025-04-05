import logging
from dataclasses import dataclass, field

import firebase_admin
from firebase_admin import App, auth, credentials
from firebase_admin.auth import ListUsersPage, UserNotFoundError, UserRecord
from firebase_admin.credentials import Certificate
from firebase_admin.exceptions import FirebaseError
from lib.schemas.firebase import FirebaseServiceAccount

logger = logging.getLogger(__name__)


@dataclass
class Firebase:
    _default_app: App | None = field(init=False, default=None)
    _app_certificate: Certificate | None = field(init=False, default=None)

    def __init__(self, service_account: FirebaseServiceAccount):
        try:
            firebase_admin.get_app()
            app_exists = True
        except ValueError:
            app_exists = False

        try:
            if app_exists is False:
                self._app_certificate = credentials.Certificate(service_account.model_dump())
                self._default_app = firebase_admin.initialize_app(
                    credential=self._app_certificate,
                )
        except IOError as err:
            logger.critical(msg="Error initializing Firebase app, certificate file not found", extra={"exception": err})
            raise err
        except ValueError as err:
            logger.critical(msg="Error initializing Firebase app", extra={"exception": err})
            raise err
        except Exception as err:
            logger.critical(msg="Error initializing Firebase app, unknown error", extra={"exception": err})
            raise err

    @property
    def app(self) -> App:
        if self._default_app is None:
            logger.error(msg="Firebase app not initialized")
            raise ValueError("Firebase app not initialized")

        return self._default_app

    def get_user_by_id(self, user_id: str) -> UserRecord:
        """
        Fetch user by ID
        :param user_id: The user ID to fetch
        :return: The user record for the given user ID
        """
        try:
            return auth.get_user(
                uid=user_id,
                app=self._default_app,
            )
        except ValueError as err:
            logger.error(msg="Error getting user by ID, User id is malformed", extra={"exception": err})
            raise err
        except UserNotFoundError as err:
            logger.error(msg="Error getting user by ID, User not found", extra={"exception": err})
            raise ConnectionAbortedError("User not found")
        except FirebaseError as err:
            logger.error(msg="Error getting user by ID", extra={"exception": err})
            raise ConnectionError("Unknown error getting user by ID")

    def get_user_by_email(self, email: str) -> UserRecord:
        """
        Fetch user by email address
        :param email: The email address to fetch
        :return: The user record for the given email
        """
        try:
            return auth.get_user_by_email(
                email=email,
                app=self._default_app,
            )
        except ValueError as err:
            logger.error(msg="Error getting user by email, email is malformed", extra={"exception": err})
            raise err
        except UserNotFoundError as err:
            logger.error(msg="Error getting user by email, User not found", extra={"exception": err})
            raise ConnectionAbortedError("User not found")
        except FirebaseError as err:
            logger.error(msg="Error getting user by email", extra={"exception": err})
            raise ConnectionError("Unknown error getting user by email")

    def get_user_by_phone_number(self, phone_number: str) -> UserRecord:
        """
        Fetch user by phone number
        :param phone_number: The phone number to fetch
        :return: The user record for the given phone number
        """
        try:
            return auth.get_user_by_phone_number(
                phone_number=phone_number,
                app=self._default_app,
            )
        except ValueError as err:
            logger.error(msg="Error getting user by phone number, phone number is malformed", extra={"exception": err})
            raise err
        except UserNotFoundError as err:
            logger.error(msg="Error getting user by phone number, User not found", extra={"exception": err})
            raise ConnectionAbortedError("User not found")
        except FirebaseError as err:
            logger.error(msg="Error getting user by phone number", extra={"exception": err})
            raise ConnectionError("Unknown error getting user by phone number")

    def get_all_users(self, max_results: int = 1000) -> ListUsersPage:
        """
        Fetch all users
        :param max_results: The maximum number of users to fetch
        :return: A list of user records for all users
        """
        try:
            return auth.list_users(app=self._default_app, max_results=max_results)
        except ValueError as err:
            logger.error(msg="Error getting all users, max_results is malformed", extra={"exception": err})
            raise err
        except FirebaseError as err:
            logger.error(msg="Error getting all users", extra={"exception": err})
            raise ConnectionError("Unknown error getting all users")
