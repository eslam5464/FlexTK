import logging
import os
import subprocess
from enum import StrEnum

import cv2
from lib.schemas.media import VideoDetails
from lib.utils.misc import convert_seconds_to_time_format

logger = logging.getLogger(__name__)


class SupportedVideoFormat(StrEnum):
    mp4 = ".mp4"
    avi = ".avi"
    mov = ".mov"
    mkv = ".mkv"
    ts = ".ts"


def get_video_details_open_cv(video_file_path: str) -> VideoDetails:
    """
    Extracts and returns details about a given video file.
    :param video_file_path: Path to the video file to extract details from.
    :return: A VideoDetails object containing video metadata.
    :raises ValueError: Input file not found
    """
    if not os.path.exists(video_file_path):
        raise ValueError("Video does not exist")

    video = cv2.VideoCapture(video_file_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps
    video_width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    video_height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    bit_rate = video.get(cv2.CAP_PROP_BITRATE)
    video.release()

    return VideoDetails(
        duration_seconds=duration,
        frames_count=frame_count,
        frames_per_second=fps,
        video_height=video_height,
        video_width=video_width,
        bit_rate=bit_rate,
    )


def extract_all_frames_open_cv(
    video_file_directory: str,
    frames_output_directory: str,
) -> None:
    """
    Extract all frames from a selected video using OpenCV
    :param video_file_directory: Path for video to extract its frames
    :param frames_output_directory: Path for the extracted frames
    :return: None
    :raise ValueError: Input video file not found
    :raise NotADirectoryError: Output directory not found
    """
    if not os.path.exists(video_file_directory):
        raise ValueError("Video does not exist")

    if not os.path.isdir(frames_output_directory):
        raise NotADirectoryError("Frames output directory does not exist")

    video_basename = os.path.basename(video_file_directory)
    video_filename, _ = os.path.splitext(video_basename)
    video = cv2.VideoCapture(video_file_directory)
    frames_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 1

    while True:
        success, frame = video.read()

        if not success:
            break

        frame_number_text = str(frame_number).zfill(len(str(frames_count)))
        frame_filename = os.path.join(
            frames_output_directory,
            f"{video_filename}_{frame_number_text}.jpg",
        )
        cv2.imwrite(filename=frame_filename, img=frame)
        frame_number += 1

    video.release()


def _validate_path_and_extensions(
    video_input_path: str,
    video_output_path: str,
) -> None:
    """
    Validates the existence of input and output paths, as well as their file extensions.
    :param video_input_path: Path to the input video file.
    :param video_output_path: Path to the output video file.
    :raises FileNotFoundError: If the input video file does not exist.
    :raises NotADirectoryError: If the directory for the output path does not exist.
    :raises ValueError: If the input or output file has an unsupported video format.
    """
    output_path_only, _ = os.path.split(video_output_path)
    _, video_input_extension = os.path.splitext(video_input_path)
    _, video_output_extension = os.path.splitext(video_output_path)
    supported_video_format: list[str] = [e.value for e in SupportedVideoFormat]

    if not os.path.exists(video_input_path):
        raise FileExistsError("Input video does not exist")

    if not os.path.isdir(output_path_only):
        raise NotADirectoryError("Output path does not exist")

    if video_input_extension not in supported_video_format:
        raise ValueError(
            f"Video extension for input is not supported, the supported extensions are {', '.join(supported_video_format)}",
        )

    if video_output_extension not in supported_video_format:
        raise ValueError(
            f"Video extension for output is not supported, the supported extensions are {', '.join(supported_video_format)}",
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


def trim_video_ffmpeg(
    video_input_path: str,
    video_output_path: str,
    start_seconds: int,
    end_seconds: int,
):
    """
    Trims the input video from the specified start to end time and saves it to the output path.
    :param video_input_path: Path to the input video file.
    :param video_output_path: Path to save the trimmed video file.
    :param start_seconds: Start time in seconds from which to begin the trim.
    :param end_seconds: End time in seconds at which to end the trim.
    :raises RuntimeError: If ffmpeg fails during the operation.
    :raises FileNotFoundError: If the input video file does not exist.
    :raises NotADirectoryError: If the directory for the output path does not exist.
    :raises ValueError: If the input or output file has an unsupported video format.
    """
    _validate_path_and_extensions(
        video_input_path=video_input_path,
        video_output_path=video_output_path,
    )
    start_time = convert_seconds_to_time_format(start_seconds).split(".")[0]
    end_time = convert_seconds_to_time_format(end_seconds).split(".")[0]

    args = [
        "ffmpeg",
        "-i",
        video_input_path,
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
        video_output_path,
        "-y",
    ]

    _run_ffmpeg_command(args)


def cut_video_ffmpeg(
    video_input_path: str,
    video_output_path: str,
    start_seconds: int,
    duration_seconds: int,
):
    """
    Trims the input video from the specified start time for a given duration and saves it to the output path.
    :param video_input_path: Path to the input video file.
    :param video_output_path: Path to save the trimmed video file.
    :param start_seconds: Start time in seconds from which to begin the trim.
    :param duration_seconds: Duration in seconds for which to trim the video.
    :raises RuntimeError: If ffmpeg fails during the operation.
    :raises FileNotFoundError: If the input video file does not exist.
    :raises NotADirectoryError: If the directory for the output path does not exist.
    :raises ValueError: If the input or output file has an unsupported video format.
    """
    _validate_path_and_extensions(
        video_input_path=video_input_path,
        video_output_path=video_output_path,
    )
    start_time = convert_seconds_to_time_format(start_seconds).split(".")[0]
    duration_time = convert_seconds_to_time_format(duration_seconds).split(".")[0]

    args = [
        "ffmpeg",
        "-i",
        video_input_path,
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
        video_output_path,
        "-y",
    ]

    _run_ffmpeg_command(args)
