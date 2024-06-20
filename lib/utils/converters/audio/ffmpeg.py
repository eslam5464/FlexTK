import os.path
import subprocess
from enum import StrEnum

from lib.wrappers.installed_apps import check_ffmpeg


class SupportedAudioFormat(StrEnum):
    mp3 = ".mp3"
    wav = ".wav"


@check_ffmpeg
def convert_audio(
        audio_file_path: str,
        output_folder: str,
        output_format: SupportedAudioFormat,
):
    """
    Converts an audio file to a specified output format and saves it to the specified output folder using ffmpeg.
    :param audio_file_path: Path to the input audio file.
    :param output_folder: Path to the folder where the converted audio will be saved.
    :param output_format: The desired output audio format (extension).
    :raises FileExistsError: If the input audio file does not exist.
    :raises NotADirectoryError: If the output folder does not exist.
    """
    if not os.path.exists(audio_file_path):
        raise FileExistsError("Input audio does not exist")

    if not os.path.isdir(output_folder):
        raise NotADirectoryError("Output folder does not exist")

    output_basename = os.path.basename(audio_file_path)
    output_filename, _ = os.path.splitext(output_basename)
    output_audio = os.path.join(output_folder, output_filename + output_format)
    args = [
        "ffmpeg",
        "-i",
        f"{audio_file_path}",
        "-y",
        "-v",
        "info",
        "-threads",
        "0",
        f"{output_audio}",
    ]
    subprocess.run(args=args, check=True)
