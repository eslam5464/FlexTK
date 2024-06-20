import os.path
import re
import subprocess

from lib.utils.libre_office import libre_office_exec
from lib.utils.wrappers.installed_apps import check_libre_office


@check_libre_office
def convert_document(
        source_document: str,
        output_dir: str,
        output_filename: str | None = None,
        timeout: float | None = None
):
    """
    Converts a given input file (typically a document) to PDF using LibreOffice.
    Requires LibreOffice to be installed on the system if it is not installed
    the function will try to install it automatically.
    :param source_document: Path to the input file to be converted.
    :param output_dir: Directory where the converted PDF file will be saved.
    :param timeout: Optional timeout for the conversion process.
    :param output_filename: Optional name for the output PDF file.
    :return: Name of the converted PDF file.
    :raises FileNotFoundError: If the input file does not exist.
    :raises NotADirectoryError: If the output directory path is invalid.
    """
    if not os.path.exists(source_document):
        raise FileNotFoundError("Input file not found")

    if os.path.isdir(output_dir):
        raise NotADirectoryError("Output path is not a directory")

    args = [libre_office_exec(), '--headless', '--convert-to', 'pdf', source_document, '--outdir', output_dir]
    process = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    filename = re.search(r'-> (.*?) using filter', process.stdout.decode())

    if not output_filename:
        return filename.group(1)

    output_root, _ = os.path.splitext(output_filename)
    output_file = os.path.join(output_dir, output_root + ".pdf")
    input_document_filename, _ = os.path.splitext(os.path.basename(source_document))
    output_file_renamed = os.path.join(output_dir, input_document_filename + ".pdf")
    os.rename(output_file, output_file_renamed)

    return output_file_renamed
