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
SCRIPT_PATH="$PYTHONPATH_SRC/app/geekbench_report/sync_cpu_model_name_to_pg.py"

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
CREATE TABLE cpu_model_names (
    cpu_model_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cpu_model TEXT
);
```
"""

import pandas as pd

from utils.geekbench_report.core.geekbench_processor_name_scraper import (
    GeekbenchProcessorNameScraper,
)
from utils.geekbench_report.database_helper import (
    get_cpu_model_name_list_from_pg,
    load_df_to_pg,
)


def sync_cpu_model_names_to_pg() -> None:
    """Sync CPU model names to PostgreSQL database."""
    scraper = GeekbenchProcessorNameScraper()
    all_cpu_model_list = scraper.scrape_all_cpu_models()
    df = pd.DataFrame(all_cpu_model_list, columns=["cpu_model"])
    # df.to_csv("cpu_model_names.csv", index=False)

    # Read existing CPU model names from database
    existing_model_list = get_cpu_model_name_list_from_pg()
    existing_model_set = set(existing_model_list)

    # Find new CPU models that need to be added
    new_models = set(df["cpu_model"]) - existing_model_set
    if new_models:
        new_df = pd.DataFrame(list(new_models), columns=["cpu_model"])
        load_df_to_pg(
            df=new_df,
            table_name="cpu_model_names",
            if_exists="append",
        )
        print(f"Added {len(new_models)} new CPU models to database")
        print(new_models)
    else:
        print("No new CPU models to add")


if __name__ == "__main__":
    sync_cpu_model_names_to_pg()
