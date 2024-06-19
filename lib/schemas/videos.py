from lib.schemas.base import BaseMetadata


class VideoDetails(BaseMetadata):
    frames_count: float
    duration_seconds: float
    frames_per_second: float
    video_width: float
    video_height: float
    bit_rate: float
