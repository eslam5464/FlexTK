from lib.schemas.base import BaseMetadata


class VideoDetails(BaseMetadata):
    frames_count: float
    duration_seconds: float
    frames_per_second: float
    video_width: float
    video_height: float
    bit_rate: float


class AudioDetails(BaseMetadata):
    duration_seconds: float | None
    bit_rate_kb: int | None
    frequency: int | None
    no_of_channels: int | None
