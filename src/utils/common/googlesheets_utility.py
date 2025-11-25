"""
Credential for Google Sheets.

GoogleSheets API usage limits:
    https://developers.google.com/sheets/api/limits
"""

import pandas as pd
import pygsheets
from pygsheets.client import Client

BIGQUERY_CREDENTIALS_FILE_PATH = "n8n-user.json"


def get_google_sheet_client() -> Client:
    """Get Google Sheets client."""
    with open(BIGQUERY_CREDENTIALS_FILE_PATH, "r") as f:
        service_account_json_str = f.read()
    return pygsheets.authorize(
        service_account_json=service_account_json_str,
    )


def load_dataframe_to_google_sheets_worksheet(
    df: pd.DataFrame,
    spreadsheet_url: str,
    worksheet_title: str,
    start_address: tuple[int, int],
    copy_head: bool = True,
) -> None:
    """
    Load DataFrame to GoogleSheets.

    The object-type-columns on GoogleSheets will be forced configured to TEXT.
    (object-type-columns: str and mixed-type contains str are considered "object")
    For following example, only column object_col will be configured as TEXT on GoogleSheets.
    >>> df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "object_col": [4, "8", 9.6],
                "float_col": [1, 2, 3.6],
            },
        )
    >>> print(df["int_col"].dtype == "object")  # False
    >>> print(df["object_col"].dtype == "object")  # True
    >>> print(df["float_col"].dtype == "object")  # False

    :param start_address:   (2, 1) denote writing data from 2nd row and column A on Worksheet
    """
    client = get_google_sheet_client()
    spreadsheet = client.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet_by_title(worksheet_title)

    # Used to generate a list of object-type-column range
    # e.g. ["A2:A524", "B2:B524", "D2:D524"]
    # worksheet.apply_format() effect only on row 2 to row 524 of column label A, etc.
    # Column index start from 1, e.g. pygsheets.Address((0, 1)).label -> A
    object_type_column_range_list = []
    for column_number, column_type in enumerate(df.dtypes):
        if column_type != "object":
            continue

        column_start_row_label = pygsheets.Address(
            (start_address[0], column_number + 1),
        ).label
        column_end_row_label = pygsheets.Address(
            (df.shape[0] + start_address[0] - 1, column_number + 1),
        ).label
        object_type_column_range_list.append(
            f"{column_start_row_label}:{column_end_row_label}",
        )

    # Upload Dataframe to let GoogleSheets generate new cells
    worksheet.set_dataframe(df=df, start=start_address, copy_head=copy_head)

    # Type of columns can be configured only if cells exist
    if object_type_column_range_list:
        worksheet.apply_format(
            object_type_column_range_list,
            format_info={
                "numberFormat": {
                    "type": pygsheets.FormatType.TEXT.value,
                },
            },
        )

        # Upload DataFrame again, then cells will follow the types configured in the last step
        worksheet.set_dataframe(df=df, start=start_address, copy_head=copy_head)


def e_gsheet_to_df(gsheet_url: str, worksheet_title: str | None = None) -> pd.DataFrame:
    """Return DataFrame from a specified Google Sheets worksheet."""
    gc = get_google_sheet_client()
    sheet = gc.open_by_url(gsheet_url)
    if worksheet_title:
        return sheet.worksheet_by_title(worksheet_title).get_as_df(numerize=False)
    return sheet.sheet1.get_as_df(numerize=False)
