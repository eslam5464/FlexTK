import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

import jwt
from keycloak import (
    KeycloakAdmin,
    KeycloakOpenID,
    KeycloakOpenIDConnection,
    KeycloakUMA,
)
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
from lib.schemas.keycloak import KeyCloakToken
from loguru import logger


class KeycloakAuth:
    def __init__(
        self,
        server_url: str,
        realm_name: str,
        client_id: str,
        client_secret: Optional[str] = None,
        admin_username: Optional[str] = None,
        admin_password: Optional[str] = None,
        verify_ssl: bool = True,
        auto_refresh: bool = True,
        cache_timeout: int = 300,  # 5 minutes
    ):
        """
        Initialize Keycloak authentication handler.
        Features:
        - User authentication and token management
        - Token validation and refresh
        - User registration and management
        - Role and permission checking
        - Session management
        - Caching for performance optimization

        Args:
            server_url (str): Keycloak server URL (e.g., 'https://keycloak.example.com/')
            realm_name (str): Realm name in Keycloak
            client_id (str): Client ID for authentication
            client_secret (str): Client secret (for confidential clients)
            admin_username (str): Admin username for user management operations
            admin_password (str): Admin password for user management operations
            verify_ssl (bool): Whether to verify SSL certificates
            auto_refresh (bool): Automatically refresh tokens when expired
            cache_timeout (int): Cache timeout in seconds for public keys and configs
        """
        self.server_url = server_url.rstrip("/")
        self.realm_name = realm_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.verify_ssl = verify_ssl
        self.auto_refresh = auto_refresh
        self.cache_timeout = cache_timeout

        # Initialize Keycloak clients
        self.keycloak_openid = KeycloakOpenID(
            server_url=server_url,
            client_id=client_id,
            realm_name=realm_name,
            client_secret_key=client_secret,
            verify=verify_ssl,
        )

        # Initialize admin client if credentials provided
        self.keycloak_admin = None
        if admin_username and admin_password:
            self.keycloak_admin = KeycloakAdmin(
                server_url=server_url,
                username=admin_username,
                password=admin_password,
                realm_name=realm_name,
                client_id=client_id,
                client_secret_key=client_secret,
                verify=verify_ssl,
            )

        # Initialize UMA client for fine-grained authorization
        self.keycloak_uma = KeycloakUMA(
            connection=KeycloakOpenIDConnection(
                server_url=server_url,
                realm_name=realm_name,
                client_id=client_id,
                client_secret_key=client_secret,
                verify=verify_ssl,
            ),
        )

        # Cache for public keys and configuration
        self._cache = {}
        self._cache_timestamps = {}

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._cache_timestamps:
            return False
        return (time.time() - self._cache_timestamps[key]) < self.cache_timeout

    def _set_cache(self, key: str, value: Any) -> None:
        """Set cache entry with timestamp."""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cache entry if valid."""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None

    def authenticate(self, username: str, password: str) -> KeyCloakToken:
        """
        Authenticate user with username and password.

        Args:
            username: User's username or email
            password: User's password

        Returns:
            dictionary containing access_token, refresh_token, and user info

        Raises:
            KeycloakAuthenticationError: If authentication fails
        """
        try:
            # Get token
            token_response = self.keycloak_openid.token(username, password)

            # Get user info
            user_info = self.keycloak_openid.userinfo(token_response["access_token"])

            # Decode token for additional info
            token_info = self.decode_token(token_response["access_token"])

            return KeyCloakToken(
                access_token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
                token_type=token_response.get("token_type", "Bearer"),
                expires_in=token_response.get("expires_in"),
                expires_at=datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600)),
                user_info=user_info,
                token_info=token_info,
                roles=token_info.get("realm_access", {}).get("roles", []),
                permissions=token_info.get("authorization", {}).get("permissions", []),
            )
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise KeycloakAuthenticationError(f"Authentication failed")

    def refresh_token(self, refresh_token: str) -> KeyCloakToken:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token information

        Raises:
            KeycloakAuthenticationError: If token refresh fails
        """
        try:
            token_response = self.keycloak_openid.refresh_token(refresh_token)

            return KeyCloakToken(
                access_token=token_response["access_token"],
                refresh_token=token_response["refresh_token"],
                token_type=token_response.get("token_type", "Bearer"),
                expires_in=token_response.get("expires_in"),
                expires_at=datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600)),
                user_info=self.keycloak_openid.userinfo(token_response["access_token"]),
                token_info=self.decode_token(token_response["access_token"]),
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise KeycloakAuthenticationError(f"Token refresh failed")

    def validate_token(self, token: str, audience: Optional[str] = None) -> dict[str, Any]:
        """
        Validate and decode access token.

        Args:
            token: Access token to validate
            audience: Expected audience (optional)

        Returns:
            Decoded token payload

        Raises:
            KeycloakAuthenticationError: If token is invalid
        """
        try:
            # Get public key (cached)
            public_key = self._get_public_key()

            # Decode and validate token
            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=audience or self.client_id,
                options={"verify_exp": True},
            )

            return decoded_token
        except jwt.ExpiredSignatureError:
            raise KeycloakAuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise KeycloakAuthenticationError(f"Invalid token")
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise KeycloakAuthenticationError(f"Token validation failed")

    def introspect_token(self, token: str) -> dict[str, Any]:
        """
        Introspect token using Keycloak's introspection endpoint.

        Args:
            token: Token to introspect

        Returns:
            Token introspection response
        """
        try:
            return self.keycloak_openid.introspect(token)
        except Exception as e:
            logger.error(f"Token introspection failed: {str(e)}")
            raise KeycloakAuthenticationError(f"Token introspection failed: {str(e)}")

    def decode_token(self, token: str, verify: bool = False) -> dict[str, Any]:
        """
        Decode token without verification (for getting payload).

        Args:
            token: Token to decode
            verify: Whether to verify token signature

        Returns:
            Decoded token payload
        """
        if verify:
            return self.validate_token(token)

        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Token decoding failed: {str(e)}")
            raise KeycloakAuthenticationError(f"Token decoding failed: {str(e)}")

    def logout(self, refresh_token: str) -> bool:
        """
        Logout user by invalidating refresh token.

        Args:
            refresh_token: User's refresh token

        Returns:
            True if logout successful
        """
        try:
            self.keycloak_openid.logout(refresh_token)
            return True
        except Exception as e:
            logger.error(f"Logout failed: {str(e)}")
            return False

    def get_user_info(self, token: str) -> dict[str, Any]:
        """
        Get user information from token.

        Args:
            token: Access token

        Returns:
            User information
        """
        try:
            return self.keycloak_openid.userinfo(token)
        except Exception as e:
            logger.error(f"Getting user info failed: {str(e)}")
            raise KeycloakAuthenticationError(f"Getting user info failed: {str(e)}")

    def has_role(self, token: str, role: str, realm_role: bool = True) -> bool:
        """
        Check if user has specific role.

        Args:
            token: Access token
            role: Role name to check
            realm_role: Whether to check realm roles (True) or client roles (False)

        Returns:
            True if user has the role
        """
        try:
            decoded_token = self.decode_token(token)

            if realm_role:
                roles = decoded_token.get("realm_access", {}).get("roles", [])
            else:
                client_access = decoded_token.get("resource_access", {})
                roles = client_access.get(self.client_id, {}).get("roles", [])

            return role in roles

        except Exception as e:
            logger.error(f"Role check failed: {str(e)}")
            return False

    def has_permission(self, token: str, resource: str, scope: str) -> bool:
        """
        Check if user has specific permission using UMA.

        Args:
            token: Access token
            resource: Resource name
            scope: Scope/action name

        Returns:
            True if user has the permission
        """
        try:
            permissions = self.keycloak_uma.resource_set_list_ids(token)
            # Implementation depends on your specific UMA configuration
            # This is a simplified version
            return True  # Implement according to your needs

        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            return False

    def create_user(self, user_data: dict[str, Any]) -> str:
        """
        Create new user (requires admin privileges).

        Args:
            user_data: User information dictionary

        Returns:
            User ID of created user

        Raises:
            KeycloakGetError: If user creation fails
        """
        if not self.keycloak_admin:
            raise ValueError("Admin client not initialized")

        try:
            user_id = self.keycloak_admin.create_user(user_data)
            logger.info(f"User created successfully: {user_id}")
            return user_id

        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            raise KeycloakGetError(f"User creation failed: {str(e)}")

    def get_user_by_id(self, user_id: str) -> dict[str, Any]:
        """Get user by ID (requires admin privileges)."""
        if not self.keycloak_admin:
            raise ValueError("Admin client not initialized")

        try:
            return self.keycloak_admin.get_user(user_id)
        except Exception as e:
            logger.error(f"Getting user failed: {str(e)}")
            raise KeycloakGetError(f"Getting user failed: {str(e)}")

    def update_user(self, user_id: str, user_data: dict[str, Any]) -> None:
        """Update user information (requires admin privileges)."""
        if not self.keycloak_admin:
            raise ValueError("Admin client not initialized")

        try:
            self.keycloak_admin.update_user(user_id, user_data)
            logger.info(f"User updated successfully: {user_id}")

        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            raise KeycloakGetError(f"User update failed: {str(e)}")

    def delete_user(self, user_id: str) -> None:
        """Delete user (requires admin privileges)."""
        if not self.keycloak_admin:
            raise ValueError("Admin client not initialized")

        try:
            self.keycloak_admin.delete_user(user_id)
            logger.info(f"User deleted successfully: {user_id}")

        except Exception as e:
            logger.error(f"User deletion failed: {str(e)}")
            raise KeycloakGetError(f"User deletion failed: {str(e)}")

    def _get_public_key(self) -> str:
        """Get public key for token validation (cached)."""
        cache_key = "public_key"

        # Check cache first
        cached_key = self._get_cache(cache_key)
        if cached_key:
            return cached_key

        try:
            # Get public key from Keycloak
            public_key = self.keycloak_openid.public_key()

            # Format public key
            formatted_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"

            # Cache the key
            self._set_cache(cache_key, formatted_key)

            return formatted_key

        except Exception as e:
            logger.error(f"Getting public key failed: {str(e)}")
            raise KeycloakGetError(f"Getting public key failed: {str(e)}")

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired without validation.

        Args:
            token: Token to check

        Returns:
            True if token is expired
        """
        try:
            decoded_token = self.decode_token(token, verify=False)
            exp_timestamp = decoded_token.get("exp", 0)
            return time.time() > exp_timestamp

        except Exception:
            return True  # Assume expired if we can't decode

    # Decorator methods for protecting routes
    def require_auth(self, f: Callable) -> Callable:
        """Decorator to require authentication for a function."""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This is a basic example - adapt to your framework
            token = self._extract_token_from_request()
            if not token:
                raise KeycloakAuthenticationError("No token provided")

            try:
                self.validate_token(token)
                return f(*args, **kwargs)
            except KeycloakAuthenticationError:
                raise

        return decorated_function

    def require_role(self, role: str, realm_role: bool = True):
        """Decorator to require specific role."""

        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                token = self._extract_token_from_request()
                if not token:
                    raise KeycloakAuthenticationError("No token provided")

                if not self.has_role(token, role, realm_role):
                    raise KeycloakAuthenticationError(f"Role '{role}' required")

                return f(*args, **kwargs)

            return decorated_function

        return decorator

    def _extract_token_from_request(self) -> Optional[str]:
        """
        Extract token from request.
        This is framework-specific - implement according to your web framework.
        """
        # Example implementation for Flask:
        # from flask import request
        # auth_header = request.headers.get('Authorization')
        # if auth_header and auth_header.startswith('Bearer '):
        #     return auth_header.split(' ')[1]
        # return None

        # For now, return None - implement based on your framework
        return None

    def get_well_known_config(self) -> dict[str, Any]:
        """Get OpenID Connect well-known configuration."""
        cache_key = "well_known_config"

        # Check cache first
        cached_config = self._get_cache(cache_key)
        if cached_config:
            return cached_config

        try:
            config = self.keycloak_openid.well_known()
            self._set_cache(cache_key, config)
            return config

        except Exception as e:
            logger.error(f"Getting well-known config failed: {str(e)}")
            raise KeycloakGetError(f"Getting well-known config failed: {str(e)}")


class KeycloakSession:
    """Helper class to manage user session with automatic token refresh."""

    def __init__(self, keycloak_auth: KeycloakAuth):
        self.keycloak_auth = keycloak_auth
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.user_info = None

    def login(self, username: str, password: str) -> bool:
        """Login and store session information."""
        try:
            auth_result = self.keycloak_auth.authenticate(username, password)
            self.access_token = auth_result.access_token
            self.refresh_token = auth_result.refresh_token
            self.expires_at = auth_result.expires_at
            self.user_info = auth_result.user_info

            return True
        except KeycloakAuthenticationError:
            return False

    def logout(self) -> None:
        """Logout and clear session."""
        if self.refresh_token:
            self.keycloak_auth.logout(self.refresh_token)

        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.user_info = None

    def get_valid_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary."""
        if not self.access_token:
            return None

        # Check if token is expired
        if self.expires_at and datetime.now() >= self.expires_at:
            # Try to refresh
            if self.refresh_token:
                try:
                    token_result = self.keycloak_auth.refresh_token(self.refresh_token)
                    self.access_token = token_result.access_token
                    self.refresh_token = token_result.refresh_token
                    self.expires_at = token_result.expires_at

                except KeycloakAuthenticationError:
                    # Refresh failed, clear session
                    self.logout()
                    return None

        return self.access_token

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with valid token."""
        return self.get_valid_token() is not None
