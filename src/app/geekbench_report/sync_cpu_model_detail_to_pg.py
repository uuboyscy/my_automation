from utils.geekbench_report.core.geekbench_processor_detail_scraper import (
    GeekbenchProcessorDetailScraper,
)
from utils.geekbench_report.database_helper import (
    get_sorted_detail_cpu_result_id_list,
    load_df_to_pg,
)


def sync_cpu_model_detail_to_pg() -> None:
    cpu_model_result_id_list = get_sorted_detail_cpu_result_id_list()
    print(cpu_model_result_id_list)
    print(len(cpu_model_result_id_list))

    for idx, cpu_model_result_id in enumerate(cpu_model_result_id_list):
        print(cpu_model_result_id, idx)
        scraper = GeekbenchProcessorDetailScraper(cpu_model_result_id)
        result = scraper.scrape_detail_page()
        # pprint(result)  # To convert to JSON-serializable dictionary

        load_df_to_pg(
            df=GeekbenchProcessorDetailScraper.detail_to_dataframe(result),
            table_name="cpu_model_details",
            if_exists="append",
        )


if __name__ == "__main__":
    sync_cpu_model_detail_to_pg()
