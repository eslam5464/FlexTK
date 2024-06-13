import pandas as pd

from .base import BaseMetadata


class ExcelDataframeSheet(BaseMetadata):
    sheet_name: str
    dataframe: pd.DataFrame
