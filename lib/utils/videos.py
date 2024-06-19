import os

import cv2

from lib.schemas.videos import VideoDetails


def get_video_details(video_file_path: str) -> VideoDetails:
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


def extract_all_frames(
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
        frame_filename = os.path.join(frames_output_directory, f"{video_filename}_{frame_number_text}.jpg")
        cv2.imwrite(filename=frame_filename, img=frame)
        frame_number += 1

    video.release()
