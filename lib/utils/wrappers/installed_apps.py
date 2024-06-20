import functools
from typing import Callable, Any

from lib.utils.ffmpeg import check_ffmpeg_installed, install_ffmpeg
from lib.utils.libre_office import check_libre_office_installed, install_libre_office


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
        if not check_libre_office_installed():
            print("LibreOffice is not installed. Installing...")
            install_libre_office()

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
        if not check_ffmpeg_installed():
            print("ffmpeg is not installed. Installing...")
            install_ffmpeg()

        value = func(*args, **kwargs)

        return value

    return wrapper
