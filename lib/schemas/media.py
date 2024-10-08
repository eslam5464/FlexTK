from .base import BaseSchema


class VideoDetails(BaseSchema):
    frames_count: float
    duration_seconds: float
    frames_per_second: float
    video_width: float
    video_height: float
    bit_rate: float


class AudioDetails(BaseSchema):
    filename: str
    duration_seconds: float | None
    bit_rate_kb: int | None
    frequency: int | None
    no_of_channels: int | None
    sound_type: str | None


class ImageDetails(BaseSchema):
    filename: str
    format_type: str
    mime_type: str
    width: int
    height: int
    color_space: str
    color_type: str
    color_type: str
    file_size: str
    no_of_pixels: str
