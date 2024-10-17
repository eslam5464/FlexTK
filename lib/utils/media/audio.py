import logging
import os
import re
import subprocess
from enum import StrEnum

from lib.schemas.media import AudioDetails
from lib.utils.misc import (
    convert_seconds_to_time_format,
    convert_time_format_to_seconds,
)
from lib.wrappers.installed_apps import check_ffmpeg

logger = logging.getLogger(__name__)


class SupportedAudioFormat(StrEnum):
    mp3 = ".mp3"
    ogg = ".ogg"
    flac = ".flac"
    wav = ".wav"


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


def _validate_path_and_extensions(
    audio_input_path: str,
    audio_output_path: str,
) -> None:
    """
    Validates the existence of input and output paths, as well as their file extensions.
    :param audio_input_path: Path to the input audio file.
    :param audio_output_path: Path to the output audio file.
    :raises FileNotFoundError: If the input audio file does not exist.
    :raises NotADirectoryError: If the directory for the output path does not exist.
    :raises ValueError: If the input or output file has an unsupported audio format.
    """
    output_path_only, _ = os.path.split(audio_output_path)
    _, audio_input_extension = os.path.splitext(audio_input_path)
    _, audio_output_extension = os.path.splitext(audio_output_path)
    supported_audio_format: list[str] = [e.value for e in SupportedAudioFormat]

    if not os.path.exists(audio_input_path):
        raise FileExistsError("Input audio does not exist")

    if not os.path.isdir(output_path_only):
        raise NotADirectoryError("Output path does not exist")

    if audio_input_extension not in supported_audio_format:
        raise ValueError(
            f"Audio extension for input is not supported, the supported extensions are {', '.join(supported_audio_format)}",
        )

    if audio_output_extension not in supported_audio_format:
        raise ValueError(
            f"Audio extension for output is not supported, the supported extensions are {', '.join(supported_audio_format)}",
        )


def _run_ffmpeg_command(args: list[str]) -> None:
    """
    Executes the ffmpeg command and handles errors.
    :param args: List of ffmpeg command arguments.
    :raises RuntimeError: If ffmpeg fails during the operation.
    """
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.error(
            f"Ffmpeg failed with error code {result.returncode}",
            extra={
                "ffmpeg_return_code": result.returncode,
                "ffmpeg_error": result.stderr,
                "ffmpeg_output": result.stdout,
            },
        )
        raise RuntimeError(f"Ffmpeg failed with error code: {result.returncode}")


def trim_audio_ffmpeg(
    audio_input_path: str,
    audio_output_path: str,
    start_seconds: int,
    end_seconds: int,
):
    """
    Trims an audio file between the specified start and end time using ffmpeg.
    :param audio_input_path: Path to the input audio file.
    :param audio_output_path: Path to the trimmed output audio file.
    :param start_seconds: Start time in seconds for trimming.
    :param end_seconds: End time in seconds for trimming.
    :raises RuntimeError: If ffmpeg fails during the operation.
    :raises FileNotFoundError: If the input audio file does not exist.
    :raises NotADirectoryError: If the directory for the output path does not exist.
    :raises ValueError: If the input or output file has an unsupported audio format.
    """
    _validate_path_and_extensions(
        audio_input_path=audio_input_path,
        audio_output_path=audio_output_path,
    )
    start_time = convert_seconds_to_time_format(start_seconds).split(".")[0]
    end_time = convert_seconds_to_time_format(end_seconds).split(".")[0]

    args = [
        "ffmpeg",
        "-i",
        audio_input_path,
        "-ss",
        f"{start_time}",
        "-to",
        f"{end_time}",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-threads",
        "0",
        audio_output_path,
        "-y",
    ]

    _run_ffmpeg_command(args)


def cut_audio_ffmpeg(
    audio_input_path: str,
    audio_output_path: str,
    start_seconds: int,
    duration_seconds: int,
):
    """
    Cuts an audio file from a start time with a given duration using ffmpeg.
    :param audio_input_path: Path to the input audio file.
    :param audio_output_path: Path to the output audio file.
    :param start_seconds: Start time in seconds for the cut.
    :param duration_seconds: Duration of the audio to extract in seconds.
    :raises RuntimeError: If ffmpeg fails during the operation.
    :raises FileNotFoundError: If the input audio file does not exist.
    :raises NotADirectoryError: If the directory for the output path does not exist.
    :raises ValueError: If the input or output file has an unsupported audio format.
    """
    _validate_path_and_extensions(
        audio_input_path=audio_input_path,
        audio_output_path=audio_output_path,
    )
    start_time = convert_seconds_to_time_format(start_seconds).split(".")[0]
    duration_time = convert_seconds_to_time_format(duration_seconds).split(".")[0]

    args = [
        "ffmpeg",
        "-i",
        audio_input_path,
        "-ss",
        f"{start_time}",
        "-t",
        f"{duration_time}",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-threads",
        "0",
        audio_output_path,
        "-y",
    ]
    _run_ffmpeg_command(args)
