"""Tasks for BigQuery."""

from enum import Enum
from typing import Literal

import pandas as pd
from google.cloud.bigquery import Client as BigQueryClient
from google.cloud.bigquery import LoadJobConfig


class WriteDispositionEnum(Enum):
    """
    Enum of parameter write_disposition for loading DataFrame to BigQuery.

    If table does not exist:
        WRITE_APPEND: Append data.
        WRITE_TRUNCATE: Truncate and then append data.
        WRITE_EMPTY: Append data only when table is empty, or raise Exception.
    If table already exists:
        All mode above create table.
    """

    WRITE_APPEND = "WRITE_APPEND"
    WRITE_TRUNCATE = "WRITE_TRUNCATE"
    WRITE_EMPTY = "WRITE_EMPTY"


def _guarantee_single_type(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee one column just has one type."""
    # To avoid `pyarrow.lib.ArrowTypeError: Expected bytes, got a 'int' object`,
    # Convert data type to str if there exists multiple types (must include str) in one column.
    # str is stored as "object", a mix of different kinds of data
    # (like integers, floats, and strings) will also have dtype "object".
    # If a column have only numeric data, it will be stored as detype "int" or "float"
    # Reference:
    #     https://stackoverflow.com/questions/21018654/strings-in-a-dataframe-but-dtype-is-object
    for column in df.columns:
        if df[column].dtype == "object":
            df[column] = df[column].apply(lambda x: str(x) if pd.notna(x) else x)

    return df


def load_dataframe_to_bigquery(
    bigquery_client: BigQueryClient,
    dataframe: pd.DataFrame,
    destination: str,
    write_disposition: Literal["WRITE_APPEND", "WRITE_TRUNCATE", "WRITE_EMPTY"],
    trans_to_singe_type: bool = True,
) -> None:
    """Load DataFrame to BigQuery."""
    if trans_to_singe_type:
        dataframe = _guarantee_single_type(dataframe)

    bigquery_client.load_table_from_dataframe(
        dataframe=dataframe,
        destination=destination,
        job_config=LoadJobConfig(write_disposition=write_disposition),
    )
