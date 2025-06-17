"""
Scrape the names of CPUs from the latest results and benchmarks pages.

The latest results page is the page that contains the latest 100 pages of CPUs.
The benchmarks page is the page that contains the benchmarks of common used CPUs.
"""

import requests
from bs4 import BeautifulSoup

# For latest 100 pages of results of CPUs. Parameters: page
LATEST_RESULTS_URL = "https://browser.geekbench.com/v6/cpu?page={page}"

# For benchmarks of common used CPUs. Only one page.
BENCHMARKS_URL = "https://browser.geekbench.com/processor-benchmarks"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}

TOTAL_PAGES_OF_LATEST_RESULTS = 100


class GeekbenchProcessorNameScraper:
    def __init__(self) -> None:
        self._total_pages = TOTAL_PAGES_OF_LATEST_RESULTS

    def _get_latest_results_url(self, page: int) -> str:
        return LATEST_RESULTS_URL.format(page=page)

    def get_total_pages(self) -> int:
        """Get the total number of pages available for the CPU."""
        return self._total_pages

    def scrape_latest_results_page(self, page: int) -> list[str]:
        response = requests.get(
            self._get_latest_results_url(page),
            headers=HEADERS,
        )
        soup = BeautifulSoup(response.text, "html.parser")
        cpu_model_set = set()
        for entry in soup.select("div.list-col-inner"):
            cpu_info = entry.select_one("span.list-col-model")
            cpu_lines = cpu_info.text.strip().split("\n") if cpu_info else []
            cpu_model = cpu_lines[0].strip() if len(cpu_lines) > 0 else None
            cpu_model_set.add(cpu_model)

        return list(cpu_model_set)

    def scrape_latest_results_multiple_pages(
        self, start_page: int = 1, end_page: int | None = None
    ) -> list[str]:
        if end_page is None:
            end_page = TOTAL_PAGES_OF_LATEST_RESULTS

        if start_page < 1:
            start_page = 1
        if end_page > TOTAL_PAGES_OF_LATEST_RESULTS:
            end_page = TOTAL_PAGES_OF_LATEST_RESULTS

        all_results = []
        for page in range(start_page, end_page + 1):
            results = self.scrape_latest_results_page(page)
            all_results.extend(results)

        return list(set(all_results))

    def scrape_benchmarks_page(self) -> list[str]:
        response = requests.get(BENCHMARKS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        cpu_model_set = set()
        for entry in soup.select("tbody tr td.name"):
            cpu_model = entry.select_one("a").text.strip()
            cpu_model_set.add(cpu_model)

        return list(cpu_model_set)

    def scrape_all_cpu_models(self) -> list[str]:
        latest_results_cpu_model_list = self.scrape_latest_results_multiple_pages()
        benchmarks_cpu_model_list = self.scrape_benchmarks_page()
        return list(set(latest_results_cpu_model_list + benchmarks_cpu_model_list))


if __name__ == "__main__":
    scraper = GeekbenchProcessorNameScraper()

    all_cpu_model_list = scraper.scrape_all_cpu_models()

    print(all_cpu_model_list)
    print("-" * 100)
    print(len(all_cpu_model_list))
