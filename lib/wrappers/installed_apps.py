import functools
import logging
from typing import Any, Callable

from lib.utils.apps import ffmpeg, image_magick, libre_office

logger = logging.getLogger(__name__)


def check_libre_office(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that ensures LibreOffice is installed before executing the decorated function.
    If LibreOffice is not installed, the decorator will install it automatically before proceeding
    with the execution of the function.
    :param func: The function to be decorated.
    :return: A wrapped function that ensures LibreOffice is installed before execution.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not libre_office.check_libre_office_installed():
            libre_office.install_libre_office()

        value = func(*args, **kwargs)

        return value

    return wrapper


def check_ffmpeg(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that ensures ffmpeg is installed before executing the decorated function.
    If ffmpeg is not installed, the decorator will install it automatically before proceeding
    with the execution of the function.

    :param func: The function to be decorated.
    :return: A wrapped function that ensures ffmpeg is installed before execution.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not ffmpeg.check_ffmpeg_installed():
            ffmpeg.install_ffmpeg()

        value = func(*args, **kwargs)

        return value

    return wrapper


def check_image_magick(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that checks if ImageMagick is installed and
    installs it if not before running the decorated function.
    :param func: The function to be decorated.
    :return: The wrapped function that ensures ImageMagick is installed before execution.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not image_magick.check_image_magick_installed():
            image_magick.install_image_magick()

        value = func(*args, **kwargs)

        return value

    return wrapper
