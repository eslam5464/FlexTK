import ast
import os

import pandas as pd
from lib.schemas.pandas_dataframe import ExcelDataframeSheet

SUPPORTED_EXCEL_EXTENSIONS = [".xlsx"]


def export_dataframes(
    all_dataframes: list[ExcelDataframeSheet],
    output_directory: str,
    output_excel_file_name: str,
) -> None:
    """
    Export the list of sheet schemas into one Excel file
    :param all_dataframes:  List of schemas contains dataframes
    :param output_directory: Path to the exported Excel file
    :param output_excel_file_name: Name of the exported Excel file
    :return: None
    :raise TypeError: File extension is not supported
    """
    _, output_file_extension = os.path.splitext(output_excel_file_name)

    if output_file_extension not in SUPPORTED_EXCEL_EXTENSIONS:
        raise TypeError(
            f"Excel file extension not supported, " f"only [{' and '.join(SUPPORTED_EXCEL_EXTENSIONS)}] is supported",
        )

    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    with pd.ExcelWriter(
        os.path.join(output_directory, output_excel_file_name),
    ) as pd_writer:
        for dataframe_entry in all_dataframes:
            dataframe_entry.dataframe.to_excel(
                excel_writer=pd_writer,
                index=False,
                sheet_name=dataframe_entry.sheet_name,
            )


def check_excel_file_if_supported(excel_filename: str) -> None:
    """
    Check if Excel file extension is supported, and it's
    determined by global variable called SUPPORTED_EXCEL_EXTENSIONS
    and checks if the file exists
    :param excel_filename: Path for the Excel file
    :return:
    """
    folder_path, file_basename = os.path.split(excel_filename)
    filename, file_extension = os.path.splitext(file_basename)

    if file_extension not in SUPPORTED_EXCEL_EXTENSIONS:
        raise TypeError(
            f"Excel file extension not supported, " f"only {' and '.join(SUPPORTED_EXCEL_EXTENSIONS)} is supported",
        )
    elif not os.path.exists(excel_filename):
        raise FileNotFoundError("Folder does not exist")


def change_dtype_from_list_to_string(dataframe: pd.DataFrame, column_name: str):
    """
    Change the data type of the given column from list to string
    :param dataframe: A dataframe that is required to be changed
    :param column_name: Name of the column that is required to change its data type
    :return: The dataframe containing the changed column
    """
    return dataframe.astype({column_name: str})


def change_dtype_from_string_to_list(
    dataframe: pd.DataFrame,
    column_name: str,
) -> pd.DataFrame:
    """
    Change the data type of the given column from string to list
    :param dataframe: A dataframe that is required to be changed
    :param column_name: Name of the column that is required to change its data type
    :return: The dataframe containing the changed column
    """

    def row_handler(row):
        if row == "None":
            return pd.NA
        else:
            return ast.literal_eval(row)

    dataframe[column_name].apply(row_handler)

    return dataframe
