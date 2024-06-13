import os

import cv2


def get_frames_count(video_file_directory: str) -> int:
    """
    Get number of frames for the specified video
    :param video_file_directory:
    :return: Number of frames
    :raise ValueError: Input file not found
    """
    if not os.path.exists(video_file_directory):
        raise ValueError("Video does not exist")

    video = cv2.VideoCapture(video_file_directory)

    return int(video.get(cv2.CAP_PROP_FRAME_COUNT))


def extract_all_frames(
        video_file_directory: str,
        frames_output_directory: str,
) -> None:
    """
    Extract all frames from a selected video using OpenCV
    :param video_file_directory: Path for video to extract its frames
    :param frames_output_directory: Path for the extracted frames
    :return: None
    :raise ValueError: Input file not found
    """
    if not os.path.exists(video_file_directory):
        raise ValueError("Video does not exist")

    video = cv2.VideoCapture(video_file_directory)
    frames_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_number = 1

    while True:
        success, frame = video.read()

        if not success:
            break

        frame_number_text = str(frame_number).zfill(len(str(frames_count)))
        frame_filename = os.path.join(frames_output_directory, f"frame_{frame_number_text}.jpg")
        cv2.imwrite(filename=frame_filename, img=frame)
        frame_number += 1

    video.release()
