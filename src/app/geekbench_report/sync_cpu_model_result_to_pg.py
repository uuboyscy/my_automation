"""
Sync CPU model results to PostgreSQL database.

Run in n8n container:
```bash
WORK_DIR="/tmp/test_git_clone"
REPO_URL="https://github.com/uuboyscy/my_automation.git"
REPO_NAME="my_automation"
PROJECT_DIR="$WORK_DIR/$REPO_NAME"
PYTHONPATH_SRC="$PROJECT_DIR/src"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
SCRIPT_PATH="$PYTHONPATH_SRC/app/geekbench_report/sync_cpu_model_result_to_pg.py"

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
echo "[INFO] Running sync_cpu_model_name_to_pg.py..."
GEEKBENCH_REPORT_POSTGRESDB_SCHEMA="$DB_POSTGRESDB_SCHEMA" \
GEEKBENCH_REPORT_POSTGRESDB_HOST="$DB_POSTGRESDB_HOST" \
GEEKBENCH_REPORT_POSTGRESDB_DATABASE="geekbench_report" \
GEEKBENCH_REPORT_POSTGRESDB_PORT="$DB_POSTGRESDB_PORT" \
GEEKBENCH_REPORT_POSTGRESDB_USER="$DB_POSTGRESDB_USER" \
GEEKBENCH_REPORT_POSTGRESDB_PASSWORD="$DB_POSTGRESDB_PASSWORD" \
PYTHONPATH="$PYTHONPATH_SRC" \
python "$SCRIPT_PATH"
```

SQL for creating table `cpu_model_names`
```
-- Table Definition
CREATE TABLE "public"."cpu_model_results" (
    "cpu_result_id" int4,
    "frequency" text,
    "cores" int2,
    "uploaded" timestamp,
    "platform" text,
    "single_core_score" int4,
    "multi_core_score" int4,
    "cpu_model_id" int4,
    "system_id" int4
);
```
"""

import time

import pandas as pd

from utils.geekbench_report.core.geekbench_processor_result_scraper import (
    GeekbenchProcessorResultScraper,
)
from utils.geekbench_report.database_helper import (
    delete_duplicated_cpu_model_result_from_pg,
    get_cpu_model_map_from_pg,
    get_last_updated_dates_of_cpu_model_df,
    get_system_map_from_pg,
    load_df_to_pg,
    update_cpu_model_names,
    update_system_names,
)


def sync_cpu_model_result_to_pg() -> None:

    last_updated_dates_of_cpu_model_df = get_last_updated_dates_of_cpu_model_df()
    system_map = get_system_map_from_pg()
    cpu_model_map = get_cpu_model_map_from_pg()

    all_df_list = []
    for idx, row in last_updated_dates_of_cpu_model_df.iterrows():
        cpu_model_name = row["cpu_model"]
        last_updated_date = row["last_uploaded"]

        print(f"[{idx}] Processing {cpu_model_name}, from {last_updated_date}")

        start_time = time.time()

        scraper = GeekbenchProcessorResultScraper(
            cpu_model_name,
            offset_date=last_updated_date,
        )
        total_pages = scraper.get_total_pages()

        print(f"Total pages available: {total_pages}")

        df = scraper.scrape_multiple_pages_until_offset_date()

        # update system_names and cpu_model_names if new one detected
        if df[~(df["system"].isin(system_map))].shape[0] > 0:
            update_system_names(df["system"].to_list())
            system_map = get_system_map_from_pg()
        if df[~(df["cpu_model"].isin(cpu_model_map))].shape[0] > 0:
            update_cpu_model_names(df["cpu_model"].to_list())
            cpu_model_map = get_cpu_model_map_from_pg()

        # system -> system_id , cpu_model -> cpu_model_id
        df["system_id"] = df["system"].map(system_map)
        df["cpu_model_id"] = df["cpu_model"].map(cpu_model_map)

        df_required_columns = df.drop(["system", "cpu_model"], axis=1)
        print(df_required_columns)

        all_df_list.append(df_required_columns)

        print(f"Total results found: {len(df_required_columns)}")
        print(f"{time.time() - start_time} seconds took.")
        print("==========")

        # Flush
        if (idx + 1) % 250 == 0:
            load_df_to_pg(
                df=pd.concat(all_df_list),
                table_name="cpu_model_results",
                if_exists="append",
            )
            delete_duplicated_cpu_model_result_from_pg()
            all_df_list = []

    # Final flush
    load_df_to_pg(
        df=pd.concat(all_df_list),
        table_name="cpu_model_results",
        if_exists="append",
    )
    delete_duplicated_cpu_model_result_from_pg()


if __name__ == "__main__":
    sync_cpu_model_result_to_pg()
