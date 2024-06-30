import os.path
from dataclasses import dataclass
from typing import Self

import cv2
import numpy as np
from cv2 import Mat  # noqa


@dataclass(init=False)
class ImageProcessingOpenCV:
    __image: Mat | np.ndarray

    def __init__(self, image_path: str):
        """
        A class for image processing tasks such as selecting, resizing,
        converting to grayscale, saving images and more.
        :param image_path: The file path to the image.
        """
        self.select_image(image_path)

    @property
    def image(self) -> Mat | np.ndarray:
        """
        Returns the currently loaded image.
        :return: The currently loaded image as a Mat or numpy ndarray.
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

        if not os.path.isdir(image_root_path):
            raise NotADirectoryError("Output path does not exist")

        cv2.imwrite(image_path, self.__image)

        return self
