"""
Update dashboard to GoogleSheets.
"""

from datetime import datetime, timedelta, timezone

import pandas as pd

from utils.common.googlesheets_utility import load_dataframe_to_google_sheets_worksheet
from utils.geekbench_report.database_helper import get_score_report_from_df


def get_update_time_df() -> pd.DataFrame:
    now = datetime.now(timezone(timedelta(hours=8)))
    return pd.DataFrame([{"Last Update": now}])


def t_convert_type_to_str(df: pd.DataFrame) -> pd.DataFrame:
    return df.fillna("").astype(str)


def sync_pg_to_googlesheets() -> None:
    score_report_df = get_score_report_from_df()
    update_time_df = get_update_time_df()

    score_report_df = t_convert_type_to_str(score_report_df)

    load_dataframe_to_google_sheets_worksheet(
        df=score_report_df,
        spreadsheet_url="https://docs.google.com/spreadsheets/d/1z9YaGs9yyJadfDJIoXaODJjOqwwMsHkJaEsLQx3J3Zo",
        worksheet_title="Score (new)",
        start_address=(2, 1),
        copy_head=False,
    )

    load_dataframe_to_google_sheets_worksheet(
        df=update_time_df,
        spreadsheet_url="https://docs.google.com/spreadsheets/d/1z9YaGs9yyJadfDJIoXaODJjOqwwMsHkJaEsLQx3J3Zo",
        worksheet_title="Data date (new)",
        start_address=(2, 1),
        copy_head=False,
    )


if __name__ == "__main__":
    sync_pg_to_googlesheets()
