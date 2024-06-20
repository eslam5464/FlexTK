import os.path
import subprocess
from enum import StrEnum

from lib.utils.wrappers.installed_apps import check_ffmpeg


class SupportedVideoFormat(StrEnum):
    mp4 = ".mp4"
    avi = ".avi"
    mov = ".mov"
    mkv = ".mkv"
    ts = ".ts"


@check_ffmpeg
def convert_video(
        video_file_path: str,
        output_folder: str,
        output_format: SupportedVideoFormat,
):
    """
    Converts a video to a specified output format and saves it to the specified output folder using ffmpeg.
    :param video_file_path: Path to the input video file.
    :param output_folder: Path to the folder where the converted video will be saved.
    :param output_format: The desired output video format (extension).
    :raises FileExistsError: If the input video file does not exist.
    :raises NotADirectoryError: If the output folder does not exist.
    """
    if not os.path.exists(video_file_path):
        raise FileExistsError("Input video does not exist")

    if not os.path.isdir(output_folder):
        raise NotADirectoryError("Output folder does not exist")

    output_basename = os.path.basename(video_file_path)
    output_filename, _ = os.path.splitext(output_basename)
    output_video = os.path.join(output_folder, output_filename + output_format)
    args = [
        "ffmpeg",
        "-hwaccel",
        "auto",
        "-i",
        f"'{video_file_path}'",
        "-y",
        "-v",
        "error",
        "-vcodec",
        "copy",
        "-acodec",
        "copy",
        "-map",
        "0:v?",
        "-map",
        "0:s?",
        "-map",
        "0:a?",
        "-stats",
        "-scodec",
        "copy",
        "-threads",
        "0",
        f"'{output_video}'",
    ]
    subprocess.run(args=args, check=True)
