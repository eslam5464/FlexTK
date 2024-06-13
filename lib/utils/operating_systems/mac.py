import subprocess


def install_homebrew():
    """
    Installs Homebrew on macOS.
    :return: None
    :raise subprocess.CalledProcessError: If the installation command fails.
    """
    try:
        subprocess.run(
            [
                '/bin/bash', '-c',
                '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'
            ], check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Homebrew: {e}")
        raise


def is_homebrew_installed():
    """
    Checks if Homebrew is installed.
    :return: bool - True if Homebrew is installed, False otherwise.
    """
    try:
        subprocess.run(['brew', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
