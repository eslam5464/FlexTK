from datetime import datetime
from typing import Any

from lib.schemas.base import BaseMetadata
from pydantic import AnyHttpUrl, Field, field_validator


class AppServiceAccount(BaseMetadata):
    app_id: int
    access_key: str
    secret_key: str


class UserProfileImage(BaseMetadata):
    small: AnyHttpUrl
    medium: AnyHttpUrl
    large: AnyHttpUrl


class UserLinks(BaseMetadata):
    self: AnyHttpUrl
    html: AnyHttpUrl
    photos: AnyHttpUrl
    likes: AnyHttpUrl
    portfolio: AnyHttpUrl
    following: AnyHttpUrl
    followers: AnyHttpUrl


class ResultUser(BaseMetadata):
    id: str
    updated_at: datetime
    username: str
    name: str
    first_name: str
    last_name: str | None
    twitter_username: str | None
    portfolio_url: str | None
    bio: str | None
    location: str | None
    links: UserLinks
    profile_image: UserProfileImage
    instagram_username: str | None
    total_collections: int
    total_likes: int
    total_photos: int
    total_promoted_photos: int
    total_illustrations: int
    total_promoted_illustrations: int
    accepted_terms_of_service: bool = Field(alias="accepted_tos")
    for_hire: bool
    social: dict

    @field_validator("updated_at", mode="before")
    def parse_datetime(cls, value: str | None):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError(str(e))
        else:
            return None


class ResultLinks(BaseMetadata):
    self: AnyHttpUrl
    html: AnyHttpUrl
    download: AnyHttpUrl
    download_location: AnyHttpUrl


class ResultUrl(BaseMetadata):
    raw: AnyHttpUrl
    full: AnyHttpUrl
    regular: AnyHttpUrl
    small: AnyHttpUrl
    thumbnail: AnyHttpUrl = Field(alias="thumb")
    amazon_s3_small: AnyHttpUrl = Field(alias="small_s3")


class ImageResult(BaseMetadata):
    id: str
    slug: str
    alternative_slugs: dict[str, str]
    created_at: datetime
    updated_at: datetime
    promoted_at: datetime | None
    width: int
    height: int
    color: str
    blur_hash: str
    description: str | None
    alt_description: str
    breadcrumbs: list
    urls: ResultUrl
    links: ResultLinks
    likes: int
    liked_by_user: bool
    current_user_collections: list
    sponsorship: None
    topic_submissions: dict[str, dict]
    asset_type: str
    uploader_data: ResultUser = Field(alias="user")
    tags: list[dict[str, Any]]

    @field_validator("created_at", "updated_at", "promoted_at", mode="before")
    def parse_datetime(cls, value: str | None):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError(str(e))
        else:
            return None


class UnsplashResponse(BaseMetadata):
    total: int
    total_pages: int
    results: list[ImageResult]
