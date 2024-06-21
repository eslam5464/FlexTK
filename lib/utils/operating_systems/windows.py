import subprocess


def is_chocolatey_installed():
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
        return False


def install_chocolatey():
    """
    Installs Chocolatey on Windows.
    :return: None
    :raise subprocess.CalledProcessError: If the installation command fails.
    """
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
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Chocolatey: {e}")
        raise e
