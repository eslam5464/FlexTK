import logging
import os
import re
import subprocess
from enum import StrEnum
from pathlib import Path

from lib.schemas.media import AudioDetails
from lib.utils.files import create_temp_file
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
    m4a = ".m4a"


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


@check_ffmpeg
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


@check_ffmpeg
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


@check_ffmpeg
def join_audio_ffmpeg(
    files_to_join: list[str],
    joined_audio_path: str,
) -> None:
    """
    Joins multiple audio files into one using ffmpeg.
    :param files_to_join: List of audio files to join.
    :param joined_audio_path: Path for the output joined audio file.
    :raises FileNotFoundError: If any input file does not exist.
    :raises ValueError: If any audio extension is unsupported or 'files_to_join' is less than 2.
    :raises NotADirectoryError: If the parent directory of the output file does not exist.
    """
    audio_path = Path(joined_audio_path)
    parent_folder = Path(audio_path).parent
    supported_audio_format: list[str] = [e.value for e in SupportedAudioFormat]
    temp_file_data = ""

    if not parent_folder.is_dir():
        raise NotADirectoryError("Output parent path for joined audio does not exist")

    if len(files_to_join) < 2:
        raise ValueError("There must be 2 or more audio files to join")

    for file_entry in files_to_join:
        file_entry_path = Path(file_entry)

        if not file_entry_path.is_file():
            raise FileNotFoundError(f"Audio file not found in {str(file_entry_path)}")

        if file_entry_path.suffix not in supported_audio_format:
            raise ValueError(
                f"Audio extension {file_entry_path.suffix} for files to join is not supported, "
                f"the supported extensions are {', '.join(supported_audio_format)}",
            )

        temp_file_data += f"file '{file_entry}'\n"

    if audio_path.suffix not in supported_audio_format:
        raise ValueError(
            f"Audio extension {audio_path.suffix} for input is not supported, "
            f"the supported extensions are {', '.join(supported_audio_format)}",
        )

    temp_text_file_path = create_temp_file(
        file_bytes=temp_file_data.encode(),
        file_extension=".txt",
    )

    args = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        temp_text_file_path,
        "-map",
        "0:a",
        "-c",
        "copy",
        joined_audio_path,
        "-y",
    ]

    try:
        _run_ffmpeg_command(args)
        logger.info(
            msg=f"Audio Joined and saved at: {joined_audio_path}",
            extra={"files_joined": f"<{'> <'.join(files_to_join)}'>"},
        )
    finally:
        os.remove(temp_text_file_path)
