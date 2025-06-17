"""
Sync CPU model names to PostgreSQL database.
"""

import os

import pandas as pd
from dotenv import load_dotenv

from utils.common.database_utility import get_postgresql_conn
from utils.geekbench_report.core.geekbench_processor_name_scraper import (
    GeekbenchProcessorNameScraper,
)

load_dotenv()

GEEKBENCH_REPORT_POSTGRESDB_SCHEMA = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_SCHEMA")
GEEKBENCH_REPORT_POSTGRESDB_HOST = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_HOST")
GEEKBENCH_REPORT_POSTGRESDB_DATABASE = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_DATABASE")
GEEKBENCH_REPORT_POSTGRESDB_PORT = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_PORT")
GEEKBENCH_REPORT_POSTGRESDB_USER = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_USER")
GEEKBENCH_REPORT_POSTGRESDB_PASSWORD = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_PASSWORD")


def sync_cpu_model_names_to_pg() -> None:
    """Sync CPU model names to PostgreSQL database."""
    scraper = GeekbenchProcessorNameScraper()
    all_cpu_model_list = scraper.scrape_all_cpu_models()
    df = pd.DataFrame(all_cpu_model_list, columns=["cpu_model"])
    df.to_csv("cpu_model_names.csv", index=False)
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        df.to_sql(
            "cpu_model_names",
            conn,
            if_exists="replace",
            index=False,
        )


if __name__ == "__main__":
    sync_cpu_model_names_to_pg()
