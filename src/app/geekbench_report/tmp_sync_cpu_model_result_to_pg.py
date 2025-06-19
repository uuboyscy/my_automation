import os
import time

import pandas as pd

from utils.geekbench_report.core.geekbench_processor_result_scraper import (
    GeekbenchProcessorResultScraper,
)
from utils.geekbench_report.database_helper import load_df_to_pg


def sync_cpu_model_result_to_pg(init: bool = False) -> None:
    # Testing local run
    proc_name_list = pd.read_csv("./cpu_model_names.csv")["cpu_model"].to_list()

    offset = 0
    if os.path.exists(".offset"):
        with open(".offset", "r") as f:
            offset_str = f.read().strip()
            if offset_str:
                offset = int(offset_str)

    print("+++++++++")
    print(f"Offset: {offset}")
    print("+++++++++")

    start_time = time.time()

    for idx, proc_name in enumerate(proc_name_list):
        # Testing local run
        if idx < offset:
            continue

        start_time = time.time()

        print(f"Processing {proc_name} [{idx}]")

        scraper = GeekbenchProcessorResultScraper(proc_name, max_pages=350)
        total_pages = scraper.get_total_pages()

        print(f"Total pages available: {total_pages}")

        df = scraper.scrape_multiple_pages()
        # df.to_csv(f"{proc_name.replace(' ', '_')}.csv", index=False)
        # Load df to Postgres
        load_df_to_pg(df=df, table_name="cpu_model_results", if_exists="append")

        print(f"Total results found: {len(df)}")
        print(f"{time.time() - start_time} seconds took.")
        print("==========")

        # Write offset
        with open(".offset", "w") as f:
            f.write(str(idx + 1))


if __name__ == "__main__":
    sync_cpu_model_result_to_pg()
    # cpu_model_name_list = get_cpu_model_name_list_from_pg()
