import time

from utils.geekbench_report.core.geekbench_processor_result_scraper import (
    GeekbenchProcessorResultScraper,
)
from utils.geekbench_report.database_helper import (
    get_last_updated_dates_of_cpu_model_df,
)


def sync_cpu_model_result_to_pg() -> None:

    last_updated_dates_of_cpu_model_df = get_last_updated_dates_of_cpu_model_df()

    for _, row in last_updated_dates_of_cpu_model_df.iterrows():
        cpu_model_name = row["cpu_model"]
        last_updated_date = row["last_uploaded"]

        print(f"Processing {cpu_model_name}, from {last_updated_date}")

        start_time = time.time()

        # delete_cpu_model_result_record_from_date_to_now(
        #     cpu_model=cpu_model_name, from_date=last_updated_date,
        # )
        scraper = GeekbenchProcessorResultScraper(
            cpu_model_name,
            offset_date=last_updated_date,
        )
        total_pages = scraper.get_total_pages()

        print(f"Total pages available: {total_pages}")

        df = scraper.scrape_multiple_pages_until_offset_date()

        print(df)
        # load_df_to_pg(df=df, table_name="cpu_model_results", if_exists="append")

        print(f"Total results found: {len(df)}")
        print(f"{time.time() - start_time} seconds took.")
        print("==========")


if __name__ == "__main__":
    sync_cpu_model_result_to_pg()
