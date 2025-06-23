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
    system_map = get_system_map_from_pg()
    cpu_model_map = get_cpu_model_map_from_pg()

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
