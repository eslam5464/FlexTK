import json
import os.path
import re
import subprocess
from dataclasses import dataclass
from enum import IntEnum
from typing import Literal, Self

import cv2
import numpy as np
import requests
from lib.schemas.media import ImageDetails
from lib.schemas.unsplash import UnsplashResponse
from lib.wrappers.installed_apps import check_image_magick
from pydantic import AnyHttpUrl
from starlette import status


class RotationEnum(IntEnum):
    clockwise_90: cv2.ROTATE_90_CLOCKWISE
    counter_clockwise_90: cv2.ROTATE_90_COUNTERCLOCKWISE
    flip_180: cv2.ROTATE_180


@dataclass(init=False)
class ImageProcessingOpenCV:
    __image: cv2.Mat | np.ndarray
    __image_extension: str
    __image_name: str

    def __init__(self, image_path: str):
        """
        A class for image processing tasks such as selecting, resizing,
        converting to grayscale, saving images and more.
        :param image_path: The file path to the image.
        """
        self.select_image(image_path)

    @property
    def image(self) -> cv2.Mat | np.ndarray:
        """
        Returns the currently loaded image.
        :return: The currently loaded image as a cv2.Mat or numpy ndarray.
        """
        return self.__image

    def select_image(self, image_path: str) -> Self:
        """
        Selects and loads an image from the specified path.
        :param image_path: The file path to the image.
        :return: The instance of the ImageProcessingOpenCV class.
        :raises FileNotFoundError: If the image file does not exist.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError("Image does not exist")

        self.__image = cv2.imread(image_path)
        self.__image_name, self.__image_extension = os.path.splitext(os.path.basename(image_path))

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

    def rotate_image(self, rotation_type: RotationEnum) -> Self:
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


@check_image_magick
def get_image_details_magick(image_path: str) -> ImageDetails:
    """
    Retrieves detailed information about an image.
    :param image_path: The file path to the image.
    :return: An instance of the ImageDetails.
    :raises FileNotFoundError: If the image file does not exist.
    """
    if not os.path.exists(image_path):
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


def get_random_images(access_key: str, count_of_images: int = 10) -> UnsplashResponse:
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
