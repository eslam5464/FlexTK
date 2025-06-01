import logging
from dataclasses import dataclass, field

import firebase_admin
import jwt
import requests
from firebase_admin import App, auth, credentials, messaging
from firebase_admin.auth import ListUsersPage, UserNotFoundError, UserRecord
from firebase_admin.credentials import Certificate
from firebase_admin.exceptions import FirebaseError
from lib.schemas.firebase import (
    FirebaseServiceAccount,
    FirebaseSignInResponse,
    FirebaseSignUpResponse,
    TokenData,
)
from lib.schemas.network import ApiResponse
from lib.utils.network import parse_response

logger = logging.getLogger(__name__)


@dataclass
class Firebase:
    _default_app: App | None = field(init=False, default=None)
    _app_certificate: Certificate | None = field(init=False, default=None)

    def __init__(self, service_account: FirebaseServiceAccount):
        """
        Initialize Firebase app
        :param service_account: Service account information
        """
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
        :raise ValueError: If user ID is malformed
        :raise ConnectionAbortedError: If the user is not found
        :raise ConnectionError: If there is an error getting the user
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
        :raise ValueError: If email is malformed
        :raise ConnectionAbortedError: If the user is not found
        :raise ConnectionError: If there is an error getting the user
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
        :raise ValueError: If phone_number is malformed
        :raise ConnectionAbortedError: If the user is not found
        :raise ConnectionError: If there is an error getting the user
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
        :raise ValueError: If max_results is malformed
        :raise ConnectionError: If there is an error getting all users
        """
        try:
            return auth.list_users(app=self._default_app, max_results=max_results)
        except ValueError as err:
            logger.error(msg="Error getting all users, max_results is malformed", extra={"exception": err})
            raise err
        except FirebaseError as err:
            logger.error(msg="Error getting all users", extra={"exception": err})
            raise ConnectionError("Unknown error getting all users")

    def notify_a_device(
        self,
        device_token: str,
        title: str,
        content: str,
    ) -> bool:
        """
        Send notification to a specific device
        :param device_token: The device token to send the notification to
        :param title: The title of the notification
        :param content: The content of the notification
        :return: True if the notification was sent successfully, False otherwise
        """
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=content,
                ),
                token=device_token,
            )

            response = messaging.send(
                message=message,
                app=self._default_app,
            )
            logger.info(f"Push notification sent successfully: {response}")
            return True
        except Exception as e:
            logger.error(f"Error sending push notification")
            logger.debug(str(e))
            return False

    def notify_multiple_devices(
        self,
        device_tokens: list[str],
        title: str,
        content: str,
    ) -> int:
        """
        Send notification to multiple devices, returns count of successful deliveries
        :param device_tokens: The device token to send the notification to
        :param title: The title of the notification
        :param content: The content of the notification
        :return: Count of successful deliveries
        """
        success_count = 0

        for tokens_chunk_index in range(0, len(device_tokens), 500):
            tokens_chunk = device_tokens[tokens_chunk_index : tokens_chunk_index + 500]

            try:
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title=title,
                        body=content,
                    ),
                    tokens=tokens_chunk,
                )
                response: messaging.BatchResponse = messaging.send_multicast(
                    multicast_message=message,
                    app=self._default_app,
                )
                success_count += response.success_count
            except FirebaseError as err:
                logger.error("Error sending push notification to multiple devices")
                logger.debug(str(err))
            except ValueError as err:
                logger.error("Error sending push notification to multiple devices")
                logger.debug(str(err))
        return success_count


class FirebaseAuth:
    _firebase_web_api_key: str | None = field(init=False, default=None)

    def __init__(self, firebase_web_api_key: str):
        """
        Initialize firebase authentication
        :param firebase_web_api_key: The firebase web api key
        """
        self._firebase_web_api_key = firebase_web_api_key
        self.validate_api_key()

    def validate_api_key(self):
        """
        Validate the firebase api key by making a request to the Firebase Authentication API
        :return: True if the API key is valid, False otherwise
        :raises ConnectionAbortedError: If the API key is not valid
        :raises ConnectionError: If there is an error validating the API key
        """
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self._firebase_web_api_key}"

        # Use deliberately invalid email format to trigger predictable error response
        payload = {
            "email": "invalid-email",
            "password": "fakePassword123",
            "returnSecureToken": True,
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.debug(msg="API key is valid")
            return False  # This line only reached if request succeeded (unlikely with invalid credentials)

        except requests.exceptions.HTTPError as ex:
            try:
                error_data = ex.response.json()
                error_msg = error_data.get("error", {}).get("message", "")

                if "INVALID_EMAIL" in error_msg:
                    # API key is valid but credentials are invalid
                    return True
                elif "API key not valid" in error_msg:
                    raise ConnectionAbortedError("API key not valid")

            except ValueError:
                logger.error(msg="Error validating API key", extra={"exception": ex})
                raise ConnectionError("Unknown error validating API key")

        except requests.exceptions.RequestException as ex:
            logger.error(msg="Error validating API key", extra={"exception": ex})
            raise ConnectionError("Unknown error validating API key")

        logger.error(msg="Error validating API key")
        raise ConnectionError("Unknown error validating API key")

    def sign_up_email_and_password(self, email: str, password: str):
        firebase_identity_base_url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key="
        request_ref = f"{firebase_identity_base_url}{self._firebase_web_api_key}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(url=request_ref, headers=headers, json=data)

        parsed_response = parse_response(response)

        id_token = parsed_response.json_data.get("idToken")

        return FirebaseSignUpResponse(
            id_token=id_token,
            decoded_token=self.decode_token(id_token),
            email=parsed_response.json_data.get("email"),
            refresh_token=parsed_response.json_data.get("refreshToken"),
            expires_in=int(parsed_response.json_data.get("expiresIn")),
            local_id=parsed_response.json_data.get("localId"),
        )

    def sign_in_email_and_password(self, email: str, password: str) -> FirebaseSignInResponse:
        """
        Sign in with email and password using firebase authentication
        :param email: email address
        :param password: password
        :return: ApiResponse
        """
        firebase_identity_base_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
        request_ref = f"{firebase_identity_base_url}{self._firebase_web_api_key}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(url=request_ref, headers=headers, json=data)
        parsed_response = parse_response(response)
        id_token = parsed_response.json_data.get("idToken")

        return FirebaseSignInResponse(
            id_token=id_token,
            decoded_token=self.decode_token(id_token),
            email=parsed_response.json_data.get("email"),
            refresh_token=parsed_response.json_data.get("refreshToken"),
            expires_in=int(parsed_response.json_data.get("expiresIn")),
            local_id=parsed_response.json_data.get("localId"),
            registered=parsed_response.json_data.get("registered"),
        )

    def send_password_reset_email(self, email: str) -> ApiResponse:
        """
        Send password reset email to the user
        :param email: email address of the user
        :return: ApiResponse object with the parsed data
        """
        firebase_identity_base_url = "https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key="
        request_ref = f"{firebase_identity_base_url}{self._firebase_web_api_key}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = {"email": email, "requestType": "PASSWORD_RESET"}
        response = requests.post(url=request_ref, headers=headers, json=data)

        return parse_response(response)

    def confirm_password_reset_code(self, oob_code: str) -> ApiResponse:
        """
        Confirm password reset code and reset the password for the user
        :param oob_code: Password reset code
        :return: ApiResponse object with the parsed data
        """
        firebase_identity_base_url = "https://identitytoolkit.googleapis.com/v1/accounts:resetPassword?key="
        request_ref = f"{firebase_identity_base_url}{self._firebase_web_api_key}"
        headers = {"content-type": "application/json; charset=UTF-8"}
        data = {"oobCode": oob_code}
        response = requests.post(url=request_ref, headers=headers, json=data)

        return parse_response(response)

    @staticmethod
    def decode_token(auth_token: str) -> TokenData | None:
        """
        Decode the token and return the token data
        :param auth_token: Authentication token
        :return: TokenData object or None
        """
        try:
            decoded_token = jwt.decode(
                jwt=auth_token,
                options={"verify_signature": False},
            )
            return TokenData(
                user_id=decoded_token.get("user_id"),
                email=decoded_token.get("email"),
                name=decoded_token.get("name"),
                issued=decoded_token.get("iat"),
                expires=decoded_token.get("exp"),
                issuer=decoded_token.get("iss"),
            )
        except jwt.DecodeError as err:
            logger.error(msg="Error decoding token", extra={"exception": err})
            return None
