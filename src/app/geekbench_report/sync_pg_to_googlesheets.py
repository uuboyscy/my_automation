"""
Update dashboard to GoogleSheets.

Run in n8n container:
```bash
WORK_DIR="/tmp/test_git_clone"
REPO_URL="https://github.com/uuboyscy/my_automation.git"
REPO_NAME="my_automation"
PROJECT_DIR="$WORK_DIR/$REPO_NAME"
PYTHONPATH_SRC="$PROJECT_DIR/src"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
SCRIPT_PATH="$PYTHONPATH_SRC/app/geekbench_report/sync_pg_to_googlesheets.py"

# === Clone or update Git repo ===
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

if [ -d "$PROJECT_DIR/.git" ]; then
  echo "[INFO] Repository already exists. Pulling latest changes..."
  cd "$PROJECT_DIR" && git pull
else
  echo "[INFO] Cloning repository..."
  git clone "$REPO_URL"
fi

# === Install Python packages ===
echo "[INFO] Installing Python dependencies..."
pip install --quiet --upgrade -r "$REQUIREMENTS" --break-system-packages

# === Set environment variables and execute Python script ===
echo "[INFO] Running sync_pg_to_googlesheets.py..."
GEEKBENCH_REPORT_POSTGRESDB_SCHEMA="$DB_POSTGRESDB_SCHEMA" \
GEEKBENCH_REPORT_POSTGRESDB_HOST="$DB_POSTGRESDB_HOST" \
GEEKBENCH_REPORT_POSTGRESDB_DATABASE="geekbench_report" \
GEEKBENCH_REPORT_POSTGRESDB_PORT="$DB_POSTGRESDB_PORT" \
GEEKBENCH_REPORT_POSTGRESDB_USER="$DB_POSTGRESDB_USER" \
GEEKBENCH_REPORT_POSTGRESDB_PASSWORD="$DB_POSTGRESDB_PASSWORD" \
PYTHONPATH="$PYTHONPATH_SRC" \
python "$SCRIPT_PATH"
```
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
