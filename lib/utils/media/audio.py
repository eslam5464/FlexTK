import os
import re
import subprocess

from lib.schemas.media import AudioDetails
from lib.utils.misc import convert_time_format_to_seconds
from lib.wrappers.installed_apps import check_ffmpeg


@check_ffmpeg
def get_audio_details_ffmpeg(audio_file_path: str) -> AudioDetails:
    """
    Retrieves detailed information about an audio file using ffprobe.
    :param audio_file_path: Path to the audio file.
    :return: An AudioDetails object containing the audio file's details.
    :raises FileNotFoundError: If the audio file does not exist.
    """
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError("Audio file does not exist")

    args = [
        "ffprobe",
        f"{audio_file_path}",
        "-hide_banner",
    ]
    output = subprocess.run(
        args=args,
        check=True,
        capture_output=True,
    )
    ffprobe_output = output.stderr.decode()

    duration_pattern = r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2}),"
    bit_rate_pattern = r"bitrate: (\d+) kb/s"
    channels_pattern = r"(\d+) channels"
    frequency_pattern = r"(\d+) Hz"
    sound_type_pattern = r"\bAudio:.*?, \d+ Hz, (stereo|mono)"

    duration_match = re.search(duration_pattern, ffprobe_output)
    bit_rate_match = re.search(bit_rate_pattern, ffprobe_output)
    frequency_match = re.search(frequency_pattern, ffprobe_output)
    channels_match = re.search(channels_pattern, ffprobe_output)
    sound_type_match = re.search(sound_type_pattern, ffprobe_output, re.IGNORECASE)

    duration = duration_match.group(1) if duration_match else None
    bit_rate = int(bit_rate_match.group(1)) if bit_rate_match else None
    no_of_channels = int(channels_match.group(1)) if channels_match else None
    frequency = int(frequency_match.group(1)) if frequency_match else None
    sound_type = sound_type_match.group(1) if sound_type_match else None

    return AudioDetails(
        filename=os.path.basename(audio_file_path),
        duration_seconds=convert_time_format_to_seconds(duration),
        bit_rate_kb=bit_rate,
        no_of_channels=no_of_channels,
        frequency=frequency,
        sound_type=sound_type,
    )
