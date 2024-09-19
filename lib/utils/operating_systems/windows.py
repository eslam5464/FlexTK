import logging
import subprocess

logger = logging.getLogger(__name__)


def is_chocolatey_installed() -> bool:
    """
    Checks if Chocolatey is installed.
    :return: bool - True if Chocolatey is installed, False otherwise.
    """
    try:
        subprocess.run(
            ["choco", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Chocolatey is not installed")

        return False


def install_chocolatey() -> None:
    """
    Installs Chocolatey on Windows.
    :return: None
    :raise subprocess.CalledProcessError: If the installation command fails.
    """
    logger.warning("Installing Chocolatey")

    try:
        subprocess.run(
            [
                "powershell.exe",
                "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                "[System.Net.ServicePointManager]::SecurityProtocol = "
                "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as err:
        logger.critical(msg="Failed to install Chocolatey", extra={"exception": str(err)})

        raise SystemError("Failed to install Chocolatey")
