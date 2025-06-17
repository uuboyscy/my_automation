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


def sync_cpu_model_names_to_pg(init: bool = False) -> None:
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
        if init:
            df.to_sql(
                "cpu_model_names",
                conn,
                if_exists="replace",
                index=False,
            )
        else:
            # Read existing CPU model names from database
            existing_df = pd.read_sql("SELECT cpu_model FROM cpu_model_names", conn)
            existing_models = set(existing_df["cpu_model"])

            # Find new CPU models that need to be added
            new_models = set(df["cpu_model"]) - existing_models
            if new_models:
                new_df = pd.DataFrame(list(new_models), columns=["cpu_model"])
                new_df.to_sql(
                    "cpu_model_names",
                    conn,
                    if_exists="append",
                    index=False,
                )
                print(f"Added {len(new_models)} new CPU models to database")
            else:
                print("No new CPU models to add")


if __name__ == "__main__":
    sync_cpu_model_names_to_pg()
