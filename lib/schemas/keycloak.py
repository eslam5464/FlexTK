from datetime import datetime
from typing import Any

from lib.schemas.base import BaseSchema


class KeyCloakToken(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    expires_at: datetime
    user_info: dict[str, Any]
    token_info: dict[str, Any]
    roles: list[str] = []
    permissions: list[dict[str, Any]] = []
