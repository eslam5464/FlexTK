import os.path
import re
import subprocess

from lib.utils.libreoffice import (
    check_libreoffice_installed,
    install_libreoffice,
    libreoffice_exec
)


def convert_document(source_document: str, output_dir: str, timeout: float | None = None):
    """
    Converts a given input file (typically a document) to PDF using LibreOffice.
    Requires LibreOffice to be installed on the system if it is not installed
    the function will try to install it automatically.
    :param source_document: Path to the input file to be converted.
    :param output_dir: Directory where the converted PDF file will be saved.
    :param timeout: Optional timeout for the conversion process.
    :return: Name of the converted PDF file.
    :raises FileNotFoundError: If the input file does not exist.
    :raises NotADirectoryError: If the output directory path is invalid.
    """
    if not os.path.exists(source_document):
        raise FileNotFoundError("Input file not found")

    if os.path.isdir(output_dir):
        raise NotADirectoryError("Output path is not a directory")

    if not check_libreoffice_installed():
        print("LibreOffice is not installed. Installing...")
        install_libreoffice()

    args = [libreoffice_exec(), '--headless', '--convert-to', 'pdf', source_document, '--outdir', output_dir]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    filename = re.search(r'-> (.*?) using filter', process.stdout.decode())

    return filename.group(1)
