from datetime import datetime

from pydantic import AnyHttpUrl, Field, field_validator

from .base import BaseSchema


class AppServiceAccount(BaseSchema):
    app_id: int
    access_key: str
    secret_key: str


class UserProfileImage(BaseSchema):
    small: AnyHttpUrl
    medium: AnyHttpUrl
    large: AnyHttpUrl


class UserLinks(BaseSchema):
    api_user: AnyHttpUrl = Field(alias="self")
    html: AnyHttpUrl
    api_user_photos: AnyHttpUrl = Field(alias="photos")
    api_user_likes: AnyHttpUrl = Field(alias="likes")
    api_user_portfolio: AnyHttpUrl = Field(alias="portfolio")
    api_user_following: AnyHttpUrl = Field(alias="following")
    api_user_followers: AnyHttpUrl = Field(alias="followers")


class SocialData(BaseSchema):
    instagram_username: str | None
    portfolio_url: str | None
    twitter_username: str | None
    paypal_email: None


class UserData(BaseSchema):
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


class ResultLinks(BaseSchema):
    api_image: AnyHttpUrl = Field(alias="self")
    html: AnyHttpUrl
    download: AnyHttpUrl
    api_download: AnyHttpUrl = Field(alias="download_location")


class ResultUrl(BaseSchema):
    raw: AnyHttpUrl
    full: AnyHttpUrl
    regular: AnyHttpUrl
    small: AnyHttpUrl
    thumbnail: AnyHttpUrl = Field(alias="thumb")
    amazon_s3_small: AnyHttpUrl = Field(alias="small_s3")


class SubmissionType(BaseSchema):
    status: str
    approved_on: str


class TopicSubmissions(BaseSchema):
    wallpapers: SubmissionType | None = None
    animals: SubmissionType | None = None
    nature: SubmissionType | None = None


class AlternativeSlugs(BaseSchema):
    en: str
    es: str
    ja: str
    fr: str
    it: str
    ko: str
    de: str
    pt: str


class CoverPhotoBreadcrumb(BaseSchema):
    slug: str
    title: str
    index: int
    type: str


class AncestrySchema(BaseSchema):
    slug: str
    pretty_slug: str


class SourceAncestry(BaseSchema):
    type: AncestrySchema = Field(alias="type")
    category: AncestrySchema
    subcategory: AncestrySchema | None = None


class TagSource(BaseSchema):
    ancestry: SourceAncestry
    title: str
    subtitle: str
    description: str
    meta_title: str
    meta_description: str
    cover_photo: "ImageResult"


class ResultTag(BaseSchema):
    type: str
    title: str
    source_data: TagSource | None = Field(default=None, alias="source")


class ImageResult(BaseSchema):
    id: str
    slug: str
    alternative_slugs: AlternativeSlugs
    created_at: datetime
    updated_at: datetime
    promoted_at: datetime | None
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
    tags: list[ResultTag] | None = None
    premium: bool | None = None
    plus: bool | None = None

    @field_validator("created_at", "updated_at", "promoted_at", mode="before")
    def parse_datetime(cls: "ImageResult", value: str | None):
        if value:
            try:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError(str(e))

        return None


class UnsplashResponse(BaseSchema):
    total: int
    total_pages: int
    results: list[ImageResult]
