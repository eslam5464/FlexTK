import subprocess
import sys

from lib.utils.ffmpeg import execute_batch_script
from lib.utils.operating_systems.mac import install_homebrew, is_homebrew_installed
from lib.utils.operating_systems.windows import (
    install_chocolatey,
    is_chocolatey_installed,
)


def install_libre_office():
    """
    Installs LibreOffice depending on the operating system.
    :return: None
    :raise OSError: If the platform is unsupported.
    :raise subprocess.CalledProcessError: If the installation command fails.
    """
    check = True

    if sys.platform == "win32":
        if not is_chocolatey_installed():
            print("Chocolatey is not installed. Installing Chocolatey...")
            install_chocolatey()

        batch_file_data = "@echo off\nchoco install libreoffice -y"
        execute_batch_script(batch_file_data)
    elif sys.platform == "darwin":
        if not is_homebrew_installed():
            print("Homebrew is not installed. Installing Homebrew...")
            install_homebrew()
        subprocess.run(["brew", "install", "--cask", "libreoffice"], check=check)
    elif sys.platform == "linux":
        subprocess.run(["sudo", "apt-get", "update"], check=check)
        subprocess.run(["sudo", "apt-get", "install", "-y", "libreoffice"], check=check)
    else:
        raise OSError("Unsupported platform")


def check_libre_office_installed():
    """
    Checks if LibreOffice is installed.
    :return: bool - True if LibreOffice is installed, False otherwise.
    """
    try:
        subprocess.run(
            [libre_office_exec(), "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def libre_office_exec():
    """
    Provides the path to the LibreOffice executable based on the operating system.

    :return: str - The path to the LibreOffice executable.
    :raise OSError: If the platform is unsupported.
    """
    if sys.platform == "win32":
        return r"C:\Program Files\LibreOffice\program\soffice.exe"
    elif sys.platform == "darwin":
        return "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    elif sys.platform == "linux":
        return "libreoffice"
    else:
        raise OSError("Unsupported platform")
