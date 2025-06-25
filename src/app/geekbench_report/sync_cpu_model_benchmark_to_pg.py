from dataclasses import asdict

import pandas as pd

from utils.geekbench_report.core.geekbench_processor_benchmark_scraper import (
    scrape_page,
)
from utils.geekbench_report.database_helper import load_df_to_pg


def sync_cpu_model_benchmarks_to_pg() -> None:
    """Sync CPU model benchmark data to PostgreSQL database."""
    benchmark_list = scrape_page()
    df = pd.DataFrame([asdict(b) for b in benchmark_list])
    load_df_to_pg(
        df,
        table_name="cpu_model_benchmarks",
        if_exists="replace",
    )  # or "append" if you want to keep old data


if __name__ == "__main__":
    sync_cpu_model_benchmarks_to_pg()
