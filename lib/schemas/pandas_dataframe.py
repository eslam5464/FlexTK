import pandas as pd

from .base import BaseSchema


class ExcelDataframeSheet(BaseSchema):
    sheet_name: str
    dataframe: pd.DataFrame
