"""
Sync CPU model names to PostgreSQL database.

Run in n8n container:
```bash
WORK_DIR="/tmp/test_git_clone"
REPO_URL="https://github.com/uuboyscy/my_automation.git"
REPO_NAME="my_automation"
PROJECT_DIR="$WORK_DIR/$REPO_NAME"
PYTHONPATH_SRC="$PROJECT_DIR/src"
REQUIREMENTS="$PROJECT_DIR/requirements.txt"
SCRIPT_PATH="$PYTHONPATH_SRC/app/geekbench_report/sync_cpu_model_detail_to_pg.py"

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
echo "[INFO] Running sync_cpu_model_detail_to_pg.py..."
GEEKBENCH_REPORT_POSTGRESDB_SCHEMA="$DB_POSTGRESDB_SCHEMA" \
GEEKBENCH_REPORT_POSTGRESDB_HOST="$DB_POSTGRESDB_HOST" \
GEEKBENCH_REPORT_POSTGRESDB_DATABASE="geekbench_report" \
GEEKBENCH_REPORT_POSTGRESDB_PORT="$DB_POSTGRESDB_PORT" \
GEEKBENCH_REPORT_POSTGRESDB_USER="$DB_POSTGRESDB_USER" \
GEEKBENCH_REPORT_POSTGRESDB_PASSWORD="$DB_POSTGRESDB_PASSWORD" \
PYTHONPATH="$PYTHONPATH_SRC" \
python "$SCRIPT_PATH"
```

SQL for creating table `cpu_model_details`
```
CREATE TABLE "public"."cpu_model_details" (
    "cpu_result_id" int4,
    "title" text,
    "upload_date" timestamp,
    "views" int4,
    "cpu_model_id" int4,
    "cpu_codename" text,
    "single_core_score" int4,
    "multi_core_score" int4,
    "system_info" jsonb,
    "cpu_info" jsonb,
    "memory_info" jsonb,
    "single_core_benchmarks" jsonb,
    "multi_core_benchmarks" jsonb
)
```
"""

from dataclasses import asdict

import pandas as pd

from utils.geekbench_report.core.geekbench_processor_detail_scraper import (
    GeekbenchProcessorDetailScraper,
)
from utils.geekbench_report.database_helper import (
    get_cpu_model_id_and_result_id_for_scraping_details_df,
    load_df_to_pg,
)


def sync_cpu_model_detail_to_pg() -> None:
    cpu_model_result_id_df = get_cpu_model_id_and_result_id_for_scraping_details_df()
    # print(cpu_model_result_id_df)
    print(len(cpu_model_result_id_df))
    print("=====")

    geekbench_processor_detail_with_model_id_list = []
    for idx, row in cpu_model_result_id_df.iterrows():
        cpu_result_id = row["cpu_result_id"]
        cpu_model_id = row["cpu_model_id"]
        print(cpu_model_id, cpu_result_id, idx)
        scraper = GeekbenchProcessorDetailScraper(cpu_result_id)
        result = scraper.scrape_detail_page()
        geekbench_processor_detail_dict = asdict(result)
        geekbench_processor_detail_dict["cpu_model_id"] = 0
        geekbench_processor_detail_with_model_id_list.append(
            geekbench_processor_detail_dict,
        )

    load_df_to_pg(
        df=pd.DataFrame(geekbench_processor_detail_with_model_id_list),
        table_name="cpu_model_details",
        if_exists="append",
    )


if __name__ == "__main__":
    sync_cpu_model_detail_to_pg()
