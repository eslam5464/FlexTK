from datetime import datetime

from pydantic import AnyHttpUrl, Field, field_validator

from .base import BaseMetadata


class AppServiceAccount(BaseMetadata):
    app_id: int
    access_key: str
    secret_key: str


class UserProfileImage(BaseMetadata):
    small: AnyHttpUrl
    medium: AnyHttpUrl
    large: AnyHttpUrl


class UserLinks(BaseMetadata):
    api_user: AnyHttpUrl = Field(alias="self")
    html: AnyHttpUrl
    api_user_photos: AnyHttpUrl = Field(alias="photos")
    api_user_likes: AnyHttpUrl = Field(alias="likes")
    api_user_portfolio: AnyHttpUrl = Field(alias="portfolio")
    api_user_following: AnyHttpUrl = Field(alias="following")
    api_user_followers: AnyHttpUrl = Field(alias="followers")


class SocialData(BaseMetadata):
    instagram_username: str | None
    portfolio_url: str | None
    twitter_username: str | None
    paypal_email: None


class UserData(BaseMetadata):
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
    social_data: SocialData = Field(alias="social")

    @field_validator("updated_at", mode="before")
    def parse_datetime(cls: "UserData", value: str | None):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError(str(e))
        else:
            return None


class ResultLinks(BaseMetadata):
    api_image: AnyHttpUrl = Field(alias="self")
    html: AnyHttpUrl
    download: AnyHttpUrl
    api_download: AnyHttpUrl = Field(alias="download_location")


class ResultUrl(BaseMetadata):
    raw: AnyHttpUrl
    full: AnyHttpUrl
    regular: AnyHttpUrl
    small: AnyHttpUrl
    thumbnail: AnyHttpUrl = Field(alias="thumb")
    amazon_s3_small: AnyHttpUrl = Field(alias="small_s3")


class SubmissionType(BaseMetadata):
    status: str
    approved_on: str


class TopicSubmissions(BaseMetadata):
    wallpapers: SubmissionType | None
    animals: SubmissionType | None
    nature: SubmissionType | None


class AlternativeSlugs(BaseMetadata):
    en: str
    es: str
    ja: str
    fr: str
    it: str
    ko: str
    de: str
    pt: str


class CoverPhotoBreadcrumb(BaseMetadata):
    slug: str
    title: str
    index: int
    type: str


class CoverPhoto(BaseMetadata):
    id: str
    slug: str
    alternative_slugs: AlternativeSlugs
    created_at: datetime
    updated_at: datetime
    promoted_at: datetime
    width: int
    height: int
    color: str
    blur_hash: str
    description: str | None
    alt_description: str
    breadcrumbs: list[CoverPhotoBreadcrumb]
    urls: ResultUrl
    links: ResultLinks
    likes: int
    liked_by_user: bool
    current_user_collections: list
    sponsorship: None
    topic_submissions: TopicSubmissions
    asset_type: str
    uploader_data: UserData = Field(alias="user")
    premium: bool | None
    plus: bool | None

    @field_validator("created_at", "updated_at", "promoted_at", mode="before")
    def parse_datetime(cls: "CoverPhoto", value: str | None):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError(str(e))
        else:
            return None


class AncestryMetadata(BaseMetadata):
    slug: str
    pretty_slug: str


class SourceAncestry(BaseMetadata):
    type: AncestryMetadata = Field(alias="type")
    category: AncestryMetadata
    subcategory: AncestryMetadata | None


class TagSource(BaseMetadata):
    ancestry: SourceAncestry
    title: str
    subtitle: str
    description: str
    meta_title: str
    meta_description: str
    cover_photo: CoverPhoto


class Tag(BaseMetadata):
    type: str
    title: str
    source_data: TagSource | None = Field(alias="source")


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
    uploader_data: UserData = Field(alias="user")
    tags: list[Tag]

    @field_validator("created_at", "updated_at", "promoted_at", mode="before")
    def parse_datetime(cls: "ImageResult", value: str | None):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError(str(e))

        return None


class UnsplashResponse(BaseMetadata):
    total: int
    total_pages: int
    results: list[ImageResult]
