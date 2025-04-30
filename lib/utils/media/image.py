import json
import logging
import os.path
import re
import subprocess
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Literal, Self

import cv2
import numpy as np
import requests
from lib.schemas.media import ImageDetails
from lib.schemas.unsplash import UnsplashResponse
from lib.wrappers.installed_apps import check_image_magick
from PIL import Image, ImageDraw, ImageFont
from pydantic import AnyHttpUrl
from requests import Response
from scrfd import SCRFD, Threshold
from starlette import status
from ultralytics import YOLO

logger = logging.getLogger(__name__)

type Number = int | float


class ImageRotationEnum(IntEnum):
    clockwise_90: cv2.ROTATE_90_CLOCKWISE
    counter_clockwise_90: cv2.ROTATE_90_COUNTERCLOCKWISE
    flip_180: cv2.ROTATE_180


class YOLOFaceDetectionEnum(StrEnum):
    v11_large = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11l-face.pt"
    v11_medium = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11m-face.pt"
    v11_small = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov11s-face.pt"
    v10_large = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov10l-face.pt"
    v10_medium = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov10m-face.pt"
    v10_small = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov10s-face.pt"
    v8_large = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8l-face.pt"
    v8_medium = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8m-face.pt"


class SCRFDFaceDetectionEnum(StrEnum):
    scrfd_10g_bnkps = "1OAXx8U8SIsBhmYYGKmD-CLXrYz_YIV-3"
    scrfd_2_5_g_bnkps = "1qnKTHMkuoWsCJ6iJeiFExGy5PSi8JKPL"
    scrfd_500m_bnkps = "13mY-c6NIShu_-4AdCo3Z3YIYja4HfNaA"


class YOLOPersonDetectionEnum(StrEnum):
    v8_nano = "https://github.com/akanametov/yolo-face/releases/download/v0.0.0/yolov8n-person.pt"


@dataclass(init=False)
class ImageProcessingOpenCV:
    __image: cv2.Mat | np.ndarray
    __image_extension: str
    __image_name: str
    __image_path: str
    __faces: list[tuple[Number, Number, Number, Number]] | None = None
    __persons: list[tuple[int, int, int, int]] | None = None
    __models_dir: Path = Path.home() / ".cache" / "flextk_models"

    def __init__(self, image_path: str):
        """
        A class for image processing tasks such as selecting, resizing,
        converting to grayscale, saving images and more.
        :param image_path: The file path to the image.
        """
        self.select_image(image_path)

        if not self.__models_dir.is_dir():
            self.__models_dir.mkdir(parents=True, exist_ok=True)

    @property
    def image(self) -> cv2.Mat | np.ndarray:
        """
        Returns the currently loaded image.
        :return: The currently loaded image as a cv2.Mat or numpy ndarray.
        """
        return self.__image

    @property
    def faces(self) -> list[tuple[int, int, int, int]] | None:
        """
        Returns the list of detected faces.
        :return: List of face bounding boxes in format (x, y, width, height)
        """
        return self.__faces

    @property
    def persons(self) -> list[tuple[int, int, int, int]] | None:
        """
        Returns the list of detected persons.
        :return: List of person bounding boxes in format (x, y, width, height)
        """
        return self.__persons

    def select_image(self, image_path: str) -> Self:
        """
        Selects and loads an image from the specified path.
        :param image_path: The file path to the image.
        :return: The instance of the ImageProcessingOpenCV class.
        :raises FileNotFoundError: If the image file does not exist.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError("Image does not exist")

        self.__image_path = image_path
        self.__image = cv2.imread(image_path)
        self.__image_name, self.__image_extension = os.path.splitext(os.path.basename(image_path))

        return self

    def detect_persons(
        self,
        output_dir: str | None = None,
        yolo_model: YOLOPersonDetectionEnum = YOLOPersonDetectionEnum.v8_nano,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 1,
        save_individual_persons: bool = False,
        confidence_threshold: float = 0.2,
    ) -> Self:
        """
        Detects persons in the loaded image using YOLO person detection model.
        :param output_dir: Directory where person images will be saved.
        :param yolo_model: YOLO person detection model to use.
        :param color: BGR color tuple for the rectangle.
        :param thickness: Thickness of the rectangle lines.
        :param save_individual_persons: If True, saves individual person crops; otherwise saves the whole image.
        :param confidence_threshold: Threshold for person detection confidence (0.0-1.0).
        :raise FileNotFoundError: If the model file does not exist.
        :raise NotADirectoryError: If the output directory does not exist.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        model_name = yolo_model.value.split("/")[-1]
        model_path = self.__models_dir / model_name

        if model_path not in list(self.__models_dir.iterdir()):
            logger.info(f"Downloading YOLO model: {yolo_model.value}")
            response = requests.get(yolo_model.value)
            if response.status_code == 200:
                with open(model_path, "wb") as model_file:
                    model_file.write(response.content)
            else:
                raise ConnectionError(f"Failed to download YOLO model: {response.status_code}, {response.reason}")

        if not model_path.is_file():
            raise FileNotFoundError(f"YOLO model file not found at {model_path}")

        # Load YOLO model
        model = YOLO(model_path)

        # Convert image to RGB (YOLO expects RGB)
        if len(self.__image.shape) == 2:
            image_rgb = cv2.cvtColor(self.__image, cv2.COLOR_GRAY2RGB)
        else:
            image_rgb = cv2.cvtColor(self.__image, cv2.COLOR_BGR2RGB)

        # Detect persons with YOLO (conf=0.001 to get all possible detections)
        results = model.predict(image_rgb, conf=confidence_threshold, verbose=False)

        persons_with_scores = []
        for result in results:
            for box in result.boxes:
                conf = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w = x2 - x1
                h = y2 - y1
                persons_with_scores.append((x1, y1, w, h, conf))

        # Store all detected persons (regardless of confidence)
        self.__persons = [(x, y, w, h) for (x, y, w, h, conf) in persons_with_scores]

        if len(self.__persons) == 0:
            logger.error(f"No persons detected in image: {self.__image_name}")
            return self

        # Create a copy to draw on
        draw_img = self.__image.copy()

        # Draw rectangles and process persons meeting confidence threshold
        for i, (x, y, w, h, conf) in enumerate(persons_with_scores):
            if conf >= confidence_threshold:
                # Draw rectangle around the person
                cv2.rectangle(draw_img, (x, y), (x + w, y + h), color, thickness)

                # Add confidence text
                confidence_text = f"Person:{conf:.0%}"
                text_size = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(draw_img, (x, y - text_size[1] - 8), (x + text_size[0], y), color, -1)
                cv2.putText(
                    draw_img,
                    confidence_text,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1,
                    cv2.LINE_AA,
                )

        if output_dir is None:
            return self

        # Check output directory
        if not os.path.isdir(output_dir):
            raise NotADirectoryError(f"Output directory {output_dir} does not exist")

        # Save image(s)
        if save_individual_persons:
            for i, (x, y, w, h, conf) in enumerate(persons_with_scores):
                if conf >= confidence_threshold:
                    person_img = self.__image[y : y + h, x : x + w]
                    person_filename = f"{self.__image_name}_person_{i}{self.__image_extension}"
                    person_path = os.path.join(output_dir, person_filename)
                    cv2.imwrite(person_path, person_img)
        else:
            output_filename = f"{self.__image_name}_persons{self.__image_extension}"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, draw_img)

        return self

    def detect_faces_scrfd(
        self,
        scrfd_model: SCRFDFaceDetectionEnum = SCRFDFaceDetectionEnum.scrfd_10g_bnkps,
        output_dir: str | None = None,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 1,
        confidence_threshold: float = 0.2,
        draw_key_points: bool = False,
    ) -> Self:
        """
        Detects faces in the loaded image using SCRFD face detection model.
        :param scrfd_model: SCRFD face detection model to use.
        :param color: BGR color tuple for the rectangle.
        :param thickness: Thickness of the rectangle lines.
        :param output_dir: Directory where face images will be saved.
        :param confidence_threshold: Threshold for face detection confidence (0.0-1.0).
        :param draw_key_points: If True, draws key points on the detected faces.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        if output_dir is not None and not Path(output_dir).is_dir():
            raise NotADirectoryError(f"Output directory {output_dir} does not exist")

        model_name = f"{scrfd_model.name}.onnx"
        model_path = self.__models_dir / model_name

        if model_path not in list(self.__models_dir.iterdir()):
            logger.info(f"Downloading SCRFD model: {scrfd_model.value}")
            self._download_from_gdrive(str(scrfd_model.value), str(model_path))

        if not model_path.is_file():
            raise FileNotFoundError(f"SCRFD model file not found at {model_path}")

        # Load SCRFD model
        face_detector = SCRFD.from_path(model_path)
        threshold = Threshold(probability=confidence_threshold)

        # Use PIL only for detection, then convert back to OpenCV
        pil_image = Image.open(self.__image_path).convert("RGB")
        faces = face_detector.detect(pil_image, threshold=threshold)

        # Create a copy to draw on
        draw_img = self.__image.copy()

        # Save faces in the image
        self.__faces = [
            (
                face.bbox.upper_left.x,
                face.bbox.upper_left.y,
                face.bbox.lower_right.x - face.bbox.upper_left.x,
                face.bbox.lower_right.y - face.bbox.upper_left.y,
            )
            for face in faces
        ]

        if len(self.__faces) == 0:
            logger.error(f"No faces detected in image: {self.__image_name}")
            return self

        for face in faces:
            bbox = face.bbox
            x1 = int(bbox.upper_left.x)
            y1 = int(bbox.upper_left.y)
            x2 = int(bbox.lower_right.x)
            y2 = int(bbox.lower_right.y)
            w = x2 - x1
            h = y2 - y1
            score = face.probability

            # Draw rectangle around the face
            cv2.rectangle(draw_img, (x1, y1), (x2, y2), color, thickness)

            # Add confidence text
            confidence_text = f"Face:{score:.0%}"
            text_size = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(draw_img, (x1, y1 - text_size[1] - 8), (x1 + text_size[0], y1), color, -1)
            cv2.putText(
                draw_img,
                confidence_text,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                1,
                cv2.LINE_AA,
            )

            # Draw key points
            if draw_key_points:
                for key_point in face.keypoints:
                    _, (points) = key_point
                    kp_x, kp_y = int(points.x), int(points.y)
                    cv2.circle(draw_img, (kp_x, kp_y), 2, (255, 0, 0), -1)

        if output_dir is not None:
            output_filename = f"{self.__image_name}_faces_{self.__image_extension}"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, draw_img)

        return self

    def detect_faces_yolo(
        self,
        output_dir: str | None = None,
        yolo_model: YOLOFaceDetectionEnum = YOLOFaceDetectionEnum.v11_large,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 1,
        save_individual_faces: bool = False,
        confidence_threshold: float = 0.2,
    ) -> Self:
        """
        Detects faces in the loaded image using YOLO face detection model.
        :param output_dir: Directory where face images will be saved.
        :param yolo_model: YOLO face detection model to use.
        :param color: BGR color tuple for the rectangle.
        :param thickness: Thickness of the rectangle lines.
        :param save_individual_faces: If True, saves individual face crops; otherwise saves the whole image.
        :param confidence_threshold: Threshold for face detection confidence (0.0-1.0).
        :raise FileNotFoundError: If the model file does not exist.
        :raise NotADirectoryError: If the output directory does not exist.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        if output_dir is not None and not Path(output_dir).is_dir():
            raise NotADirectoryError(f"Output directory {output_dir} does not exist")

        model_name = yolo_model.value.split("/")[-1]
        model_path = self.__models_dir / model_name

        if model_path not in list(self.__models_dir.iterdir()):
            logger.info(f"Downloading YOLO model: {yolo_model.value}")
            response = requests.get(str(yolo_model.value))
            if response.status_code == 200:
                with open(model_path, "wb") as model_file:
                    model_file.write(response.content)
            else:
                raise ConnectionError(f"Failed to download YOLO model: {response.status_code}, {response.reason}")

        if not model_path.is_file():
            raise FileNotFoundError(f"YOLO model file not found at {model_path}")

        # Load YOLO model
        model = YOLO(model_path)

        # Convert image to RGB (YOLO expects RGB)
        if len(self.__image.shape) == 2:
            image_rgb = cv2.cvtColor(self.__image, cv2.COLOR_GRAY2RGB)
        else:
            image_rgb = cv2.cvtColor(self.__image, cv2.COLOR_BGR2RGB)

        # Detect faces with YOLO (conf=0.001 to get all possible detections)
        results = model.predict(image_rgb, conf=confidence_threshold, verbose=False)

        persons_with_scores = []
        for result in results:
            for box in result.boxes:
                conf = box.conf.item()
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                w = x2 - x1
                h = y2 - y1
                persons_with_scores.append((x1, y1, w, h, conf))

        # Store all detected faces (regardless of confidence)
        self.__faces = [(x, y, w, h) for (x, y, w, h, conf) in persons_with_scores]

        if len(self.__faces) == 0:
            logger.error(f"No faces detected in image: {self.__image_name}")
            return self

        # Create a copy to draw on
        draw_img = self.__image.copy()

        # Draw rectangles and process faces meeting confidence threshold
        for i, (x, y, w, h, conf) in enumerate(persons_with_scores):
            if conf >= confidence_threshold:
                # Draw rectangle around the face
                cv2.rectangle(draw_img, (x, y), (x + w, y + h), color, thickness)

                # Add confidence text
                confidence_text = f"Face:{conf:.0%}"
                text_size = cv2.getTextSize(confidence_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(draw_img, (x, y - text_size[1] - 8), (x + text_size[0], y), color, -1)
                cv2.putText(
                    draw_img,
                    confidence_text,
                    (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1,
                    cv2.LINE_AA,
                )

        if output_dir is None:
            return self

        # Save image(s)
        if save_individual_faces:
            for i, (x, y, w, h, conf) in enumerate(persons_with_scores):
                if conf >= confidence_threshold:
                    face_img = self.__image[y : y + h, x : x + w]
                    face_filename = f"{self.__image_name}_face_{i}{self.__image_extension}"
                    face_path = os.path.join(output_dir, face_filename)
                    cv2.imwrite(face_path, face_img)
        else:
            output_filename = f"{self.__image_name}_faces{self.__image_extension}"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, draw_img)

        return self

    def resize_image(self, width: int, height: int) -> Self:
        """
        Resizes the selected image to the specified width and height.
        :param width: The desired width of the resized image.
        :param height: The desired height of the resized image.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        self.__image = cv2.resize(self.__image, (width, height))

        return self

    def rotate_image(self, rotation_type: ImageRotationEnum) -> Self:
        """
        Rotates the selected image based on the specified rotation type.
        :param rotation_type: The type of rotation to apply, as defined in the RotationEnum.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        self.__image = cv2.rotate(self.__image, rotation_type)

        return self

    def convert_to_grayscale(self) -> Self:
        """
        Converts the selected image to grayscale.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        self.__image = cv2.cvtColor(self.__image, cv2.COLOR_BGR2GRAY)

        return self

    def save_image(self, image_path: str) -> Self:
        """
        Saves the processed image to the specified output path.
        :param image_path: The file path where the image will be saved.
        :return: The instance of the ImageProcessingOpenCV class.
        :raises NotADirectoryError: If the output path does not exist.
        """
        image_root_path, _ = os.path.split(image_path)
        _, image_extension = os.path.splitext(image_path)

        if not os.path.isdir(image_root_path):
            raise NotADirectoryError("Output path does not exist")

        if image_extension != self.__image_extension:
            raise ValueError(
                f"Image extension {image_extension} not " f"the same as selected image {self.__image_extension}",
            )

        cv2.imwrite(image_path, self.__image)

        return self

    def show_image(self) -> Self:
        """
        Displays the selected image in a window.
        :return: The instance of the ImageProcessingOpenCV class.
        """
        cv2.imshow(winname=self.__image_name, mat=self.__image)
        cv2.waitKey(0)

        return self

    @staticmethod
    def _download_from_gdrive(model_id: str, destination: str):
        url = "https://docs.google.com/uc?export=download"

        def get_confirm_token(token_response: Response):
            for key, value in token_response.cookies.items():
                if key.startswith("download_warning"):
                    return {"confirm": value}

            if "text/html" in token_response.headers["Content-Type"]:
                m = re.search('.*confirm=([^"]*)', token_response.text, re.M)
                if m and m.groups():
                    return {"confirm": m.groups()[0]}
                else:
                    params = {}
                    matches = re.findall(
                        '<input type="hidden" name="(?P<name>[^"]*)" value="(?P<value>[^"]*)".*?>',
                        token_response.text,
                        re.M,
                    )
                    for match in matches:
                        params[match[0]] = match[1]
                    return params
            return None

        def save_response_content(token_response: Response, download_folder: str):
            chunk_size = 1024

            with open(download_folder, "wb") as f:
                for chunk in token_response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

        session = requests.Session()
        response = session.get(url, params={"id": model_id}, stream=True)
        token = get_confirm_token(response)

        if token:
            if len(token) > 1:
                url = "https://drive.usercontent.google.com/download"

            token["id"] = model_id
            headers = {"Range": "bytes=0-"}
            response = session.get(url, params=token, headers=headers, stream=True)

        if response.status_code not in (200, 206):
            logger.error(f"Failed to download file, {response.text}")
            raise RuntimeError(f"Failed downloading file {model_id}")

        save_response_content(response, destination)


@check_image_magick
def get_image_details_magick(image_path: str) -> ImageDetails:
    """
    Retrieves detailed information about an image.
    :param image_path: The file path to the image.
    :return: An instance of the ImageDetails.
    :raises FileNotFoundError: If the image file does not exist.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError("Image does not exist")

    args = [
        "magick",
        "identify",
        "-verbose",
        image_path,
    ]
    output = subprocess.run(
        args=args,
        check=True,
        capture_output=True,
    )
    magick_output = output.stdout.decode()
    info_dict = {}

    for line in magick_output.splitlines():
        match = re.match(r"^\s*(\w[\w ]*): (.+)$", line)
        if match:
            key = match.group(1).strip().lower()
            value = match.group(2).strip()
            info_dict[key] = value

    return ImageDetails(
        filename=info_dict.get("filename"),
        format_type=info_dict.get("format"),
        width=int(info_dict.get("geometry").split("x")[0]),
        height=int(info_dict.get("geometry").split("x")[1].split("+")[0]),
        color_space=info_dict.get("colorspace"),
        color_type=info_dict.get("type"),
        mime_type=info_dict.get("mime type"),
        file_size=info_dict.get("filesize"),
        no_of_pixels=info_dict.get("number pixels"),
    )


def _get_images_from_unsplash(unsplash_url: str, access_key: str):
    """
    Internal function to fetch images from Unsplash based on a provided URL and access key.
    :param unsplash_url: The URL for the Unsplash API request.
    :param access_key: The access key for the Unsplash API.
    :return: An instance of UnsplashResponse containing the fetched images.
    :raises ConnectionRefusedError: If the request is unacceptable or missing permissions.
    :raises ConnectionAbortedError: If the access token is invalid.
    :raises ConnectionError: If there is an internal error with Unsplash or an unknown response code.
    """
    unsplash_response = requests.get(
        url=unsplash_url,
        headers={"Authorization": f"Client-ID {access_key}"},
    )

    if unsplash_response.status_code == status.HTTP_200_OK:
        pass
    elif unsplash_response.status_code == status.HTTP_400_BAD_REQUEST:
        raise ConnectionRefusedError(f"The request was unacceptable with reason: {unsplash_response.reason}")
    elif unsplash_response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise ConnectionAbortedError(f"Invalid access token")
    elif unsplash_response.status_code == status.HTTP_403_FORBIDDEN:
        raise ConnectionRefusedError(f"Missing permissions with reason: {unsplash_response.reason}")
    elif unsplash_response.status_code == status.HTTP_404_NOT_FOUND:
        raise ConnectionRefusedError(f"The requested resource does not exist with reason: {unsplash_response.reason}")
    elif unsplash_response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE]:
        raise ConnectionError(f"Unsplash internal error with reason: {unsplash_response.reason}")
    else:
        raise ConnectionError(
            f"Unknown response with code : {unsplash_response.status_code} " f"& reason: {unsplash_response.reason}",
        )

    unsplash_response_dict: dict = json.loads(unsplash_response.content)

    return UnsplashResponse.model_validate(unsplash_response_dict)


def get_images_by_search_unsplash(
    search_text: str,
    access_key: str,
) -> UnsplashResponse:
    """
    Searches for images on Unsplash based on the provided search text and access key.
    :param search_text: The text to search for images.
    :param access_key: The access key for the Unsplash API.
    :return: An instance of UnsplashResponse containing the search results.
    :raises ConnectionRefusedError: If the request is unacceptable or missing permissions.
    :raises ConnectionAbortedError: If the access token is invalid.
    :raises ConnectionError: If there is an internal error with Unsplash or an unknown response code.
    """
    unsplash_photos_api_url = "https://api.unsplash.com/search/photos"
    unsplash_search_parameter = f"?query={search_text}"
    unsplash_url = unsplash_photos_api_url + unsplash_search_parameter

    return _get_images_from_unsplash(unsplash_url=unsplash_url, access_key=access_key)


def get_random_images_unsplash(access_key: str, count_of_images: int = 10) -> UnsplashResponse:
    """
    Retrieves a specified number of random images from Unsplash
    :param access_key: The access key for the Unsplash API
    :param count_of_images: The number of random images to retrieve (default is 10, maximum is 30)
    :return: An instance of UnsplashResponse containing the random images
    :raises ConnectionRefusedError: If the request is unacceptable or missing permissions.
    :raises ConnectionAbortedError: If the access token is invalid.
    :raises ConnectionError: If there is an internal error with Unsplash or an unknown response code.
    """
    count_of_images = 30 if count_of_images > 30 else count_of_images
    unsplash_photos_api_url = "https://api.unsplash.com/photos/random"
    unsplash_search_parameter = f"?count={count_of_images}"
    unsplash_url = unsplash_photos_api_url + unsplash_search_parameter

    return _get_images_from_unsplash(unsplash_url=unsplash_url, access_key=access_key)


def download_images_by_search_unsplash(
    search_text: str,
    access_key: str,
    images_download_path: str,
    download_size: Literal["full", "regular", "small", "thumbnail"] = "regular",
) -> None:
    """
    Downloads images from Unsplash based on the provided search text and access key,
    saving them to the specified download path.
    :param search_text: The text to search for images.
    :param access_key: The access key for the Unsplash API.
    :param images_download_path: The path where the images will be downloaded.
    :param download_size: The size of the images to download (default is "regular").
    :raises NotADirectoryError: If the images download path is not a directory.
    """
    if not os.path.isdir(images_download_path):
        raise NotADirectoryError("Images download path is not a directory")

    unsplash_model = get_images_by_search_unsplash(
        search_text=search_text,
        access_key=access_key,
    )

    for result_entry in unsplash_model.results:
        image_url: AnyHttpUrl = result_entry.urls.model_dump().get(download_size, "regular")
        image_extension = result_entry.urls.regular.__str__().split("&fm=")[-1].split("&")[0]
        image_path = os.path.join(images_download_path, f"{result_entry.slug}.{image_extension}")

        with open(image_path, "wb") as image_file:
            image_file_response = requests.get(image_url, stream=True)

            for block in image_file_response.iter_content(1024):
                if not block:
                    break

                image_file.write(block)
