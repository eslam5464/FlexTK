import logging
import subprocess

logger = logging.getLogger(__name__)


def install_homebrew() -> None:
    """
    Installs Homebrew on macOS.
    :return: None
    :raise subprocess.CalledProcessError: If the installation command fails.
    """
    logger.warning("Installing Homebrew")

    try:
        subprocess.run(
            [
                "/bin/bash",
                "-c",
                "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as err:
        logger.critical(msg="Failed to install Homebrew", extra={"exception": str(err)})

        raise SystemError("Failed to install Homebrew")


def is_homebrew_installed() -> bool:
    """
    Checks if Homebrew is installed.
    :return: bool - True if Homebrew is installed, False otherwise.
    """
    try:
        subprocess.run(
            ["brew", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Homebrew is not installed")

    return False
