import hashlib
import json
import mimetypes
import os
from tempfile import NamedTemporaryFile
from typing import Any, Literal

import crc32c
import pandas as pd
from pandera.api.base.model import MetaModel


def create_temp_file(file_bytes: bytes, file_extension: str) -> str:
    """
    Creates a temporary file with the given file extension and its bytes
    :param file_extension: File extension for the temp file
    :param file_bytes: Bytes for the temp file
    :return: Path of the temporary file
    """
    with NamedTemporaryFile(
        delete=False,
        suffix=file_extension,
    ) as temp_file:
        file_path = temp_file.name
        temp_file.write(file_bytes)

    return file_path


def remove_files(files_path: list[str]) -> list:
    """
    Remove files from the given list of files
    :param files_path: List of files to remove
    :return: List of files that were not found
    """
    not_found_files = []

    for file_entry in files_path:
        if os.path.exists(file_entry):
            os.remove(file_entry)
        else:
            not_found_files.append(file_entry)

    return not_found_files


def read_json_file(file_location: str) -> Any:
    """
    Reads the specified JSON file and return its value
    :param file_location: Path for JSON file
    :return: Data from the file
    :raise FileNotFoundError: JSON file does not exist
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"JSON file not found in {file_location}")

    with open(file_location) as json_file:
        return json.load(json_file)


def read_csv_file(
    file_location: str,
    schema_model: MetaModel | None = None,
) -> pd.DataFrame:
    """
    Reads the csv file from the specified location and return it as a validated pandas dataframe against
    the pandera schema if specified
    :param file_location: path for the csv file
    :param schema_model: schema to validate with the csv file
    :return: Pandas dataframe contains the csv file data
    :raise FileNotFoundError: File not found in the specified location
    :raise ValueError: File extension is not .csv
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"CSV file not found in {file_location}")

    file_extension = os.path.splitext(file_location)[-1]
    supported_extension = ".csv"

    if file_extension != supported_extension:
        raise ValueError(
            f"The file's extension '{file_extension}' is not a supported '{supported_extension}'",
        )

    csv_data = pd.read_csv(file_location)

    if schema_model:
        csv_data = schema_model(csv_data)

    return csv_data


def read_excel_file(
    file_location: str,
    sheet_name: str,
    schema_model: MetaModel | None = None,
    engine: Literal["xlrd", "openpyxl", "pyxlsb"] = "openpyxl",
) -> pd.DataFrame:
    """
    Reads an Excel file from the specified location and sheet, optionally
    validating its content against a provided schema model.
    :param file_location: The path to the Excel file to be read.
    :param sheet_name: The name of the sheet to be read from the Excel file.
    :param schema_model: An optional schema model for validating the content of the Excel file. Default is None.
    :param engine: The engine to use for reading the Excel file.
    :return: A pandas DataFrame containing the data from the specified sheet of the Excel file.
    :raises FileNotFoundError: If the specified file does not exist.
    :raises ValueError: If the file extension is not supported.
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"CSV file not found in {file_location}")

    file_extension = os.path.splitext(file_location)[-1]
    supported_extension = [".xlsx", ".xls", ".xlsb"]

    if file_extension not in supported_extension:
        raise ValueError(
            f"The extension '{file_extension}' the only supported are '{supported_extension}'",
        )

    csv_data = pd.read_excel(io=file_location, sheet_name=sheet_name, engine=engine)

    if schema_model:
        csv_data = schema_model(csv_data)

    return csv_data


def get_file_type(file_location: str) -> str | None:
    """
    Determines the MIME type of the file given its location.
    :param file_location: The file path to determine the type of.
    :return: The MIME type of the file as a string if it can be determined, otherwise None.
    :raises FileNotFoundError: If the specified file does not exist.
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"File not found in {file_location}")

    file_type, _ = mimetypes.guess_type(file_location)

    return file_type


def calculate_md5_hash(file_location: str) -> str:
    """
    Calculates the MD5 hash of a file.
    :param file_location: The file path of the input file for which the MD5 hash is to be calculated.
    :return: The computed MD5 hash of the file as a hexadecimal string.
    :raises FileNotFoundError: If the specified file does not exist at the provided file location.
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"File not found in {file_location}")

    hash_md5 = hashlib.md5()

    with open(file_location, "rb") as file_binary:
        for chunk in iter(lambda: file_binary.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def calculate_crc32c_checksum(file_location: str) -> int:
    """
    Calculates the CRC32C checksum of a file.
    :param file_location: The file path of the input file for which the CRC32C hash is to be calculated.
    :return: The computed CRC32C checksum of the file as an integer.
    :raises FileNotFoundError: If the specified file does not exist at the provided file location.
    """
    if not os.path.exists(file_location):
        raise FileNotFoundError(f"File not found in {file_location}")

    with open(file_location, "rb") as file_bytes:
        data = file_bytes.read()

    return crc32c.crc32c(data)
