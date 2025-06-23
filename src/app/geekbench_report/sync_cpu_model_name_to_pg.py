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

from utils.geekbench_report.core.geekbench_processor_name_scraper import (
    GeekbenchProcessorNameScraper,
)
from utils.geekbench_report.database_helper import update_cpu_model_names


def sync_cpu_model_names_to_pg() -> None:
    """Sync CPU model names to PostgreSQL database."""
    scraper = GeekbenchProcessorNameScraper()
    all_cpu_model_list = scraper.scrape_all_cpu_models()
    update_cpu_model_names(all_cpu_model_list)


if __name__ == "__main__":
    sync_cpu_model_names_to_pg()
