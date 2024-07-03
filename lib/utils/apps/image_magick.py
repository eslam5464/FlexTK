import subprocess
import sys

from lib.utils.apps.base import PlatformTypeEnum
from lib.utils.misc import execute_batch_script
from lib.utils.operating_systems.mac import install_homebrew, is_homebrew_installed
from lib.utils.operating_systems.windows import (
    install_chocolatey,
    is_chocolatey_installed,
)


def install_image_magick() -> None:
    """
    Installs ImageMagick on the current system.
    :raises OSError: If the platform is not supported.
    """
    check = True

    if sys.platform == PlatformTypeEnum.windows:
        if not is_chocolatey_installed():
            print("Chocolatey is not installed. Installing Chocolatey...")
            install_chocolatey()

        batch_file_data = "@echo off\nchoco install imagemagick -y"
        execute_batch_script(batch_file_data)
    elif sys.platform == PlatformTypeEnum.mac:
        if not is_homebrew_installed():
            print("Homebrew is not installed. Installing Homebrew...")
            install_homebrew()
        subprocess.run(["brew", "install", "imagemagick"], check=check)
    elif sys.platform == PlatformTypeEnum.linux:
        subprocess.run(["sudo", "apt-get", "update"], check=check)
        subprocess.run(["sudo", "apt-get", "install", "-y", "imagemagick"], check=check)
    else:
        raise OSError("Unsupported platform")


def check_image_magick_installed() -> bool:
    """
    Checks if ImageMagick is installed on the system.
    :return: True if ImageMagick is installed, False otherwise.
    """
    try:
        subprocess.run(
            ["magick", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
