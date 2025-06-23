import time

from utils.geekbench_report.core.geekbench_processor_result_scraper import (
    GeekbenchProcessorResultScraper,
)
from utils.geekbench_report.database_helper import (
    delete_cpu_model_result_record_from_date_to_now,
    get_cpu_model_map_from_pg,
    get_last_updated_dates_of_cpu_model_df,
    get_system_map_from_pg,
    load_df_to_pg,
    update_cpu_model_names,
    update_system_names,
)


def sync_cpu_model_result_to_pg() -> None:

    last_updated_dates_of_cpu_model_df = get_last_updated_dates_of_cpu_model_df()

    for idx, row in last_updated_dates_of_cpu_model_df.iterrows():
        cpu_model_name = row["cpu_model"]
        last_updated_date = row["last_uploaded"]

        print(f"[{idx}] Processing {cpu_model_name}, from {last_updated_date}")

        start_time = time.time()

        delete_cpu_model_result_record_from_date_to_now(
            cpu_model=cpu_model_name,
            from_date=last_updated_date,
        )

        scraper = GeekbenchProcessorResultScraper(
            cpu_model_name,
            offset_date=last_updated_date,
        )
        total_pages = scraper.get_total_pages()

        print(f"Total pages available: {total_pages}")

        df = scraper.scrape_multiple_pages_until_offset_date()

        # update system_names if new system detected
        update_system_names(df["system"])
        # system -> system_id
        df["system_id"] = df["system"].map(get_system_map_from_pg())
        # update cpu_model_names if new cpu_model detected
        update_cpu_model_names(df["cpu_model"])
        # cpu_model -> cpu_model_id
        df["cpu_model_id"] = df["cpu_model"].map(get_cpu_model_map_from_pg())

        print(df.drop(["system", "cpu_model"], axis=1))
        load_df_to_pg(
            df=df.drop(["system", "cpu_model"], axis=1),
            table_name="cpu_model_results",
            if_exists="append",
        )

        print(f"Total results found: {len(df)}")
        print(f"{time.time() - start_time} seconds took.")
        print("==========")


if __name__ == "__main__":
    sync_cpu_model_result_to_pg()
