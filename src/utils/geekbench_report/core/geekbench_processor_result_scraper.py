from dataclasses import dataclass

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pandas import Timestamp

BASE_URL = "https://browser.geekbench.com/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}


@dataclass
class GeekbenchProcessorResult:
    cpu_id: str | None
    system: str | None
    cpu_model: str | None
    frequency: str | None
    cores: int | None
    uploaded: Timestamp | None
    platform: str | None
    single_core_score: int | None
    multi_core_score: int | None
    url: str | None


class GeekbenchProcessorResultScraper:
    def __init__(self, cpu_name: str, max_pages: int | None = None) -> None:
        self.cpu_name = cpu_name
        self._total_pages = None
        self.max_pages = max_pages

    def _get_base_url(self) -> str:
        return BASE_URL

    def _get_params(self, page: int) -> dict[str, str]:
        return {"q": self.cpu_name, "page": str(page)}

    def _parse_entry(self, entry) -> GeekbenchProcessorResult:
        system_a = entry.select_one("a[href^='/v6/cpu/']")
        system = system_a.text.strip() if system_a else None
        cpuid_url = system_a["href"] if system_a and system_a.has_attr("href") else None
        url = f"https://browser.geekbench.com{cpuid_url}" if cpuid_url else None

        cpu_info = entry.select_one("span.list-col-model")
        cpu_lines = cpu_info.text.strip().split("\n") if cpu_info else []
        cpu_model = cpu_lines[0].strip() if len(cpu_lines) > 0 else None
        cpu_freq = cpu_lines[1].strip() if len(cpu_lines) > 1 else None
        cpu_cores = (
            int(cpu_lines[2].strip("() \n").replace("cores", "").strip())
            if len(cpu_lines) > 2
            else None
        )

        uploaded_text = entry.select_one(
            "span.list-col-subtitle:-soup-contains('Uploaded') + span"
        )
        # Some date string be like "Feb 28, 2023\n\nrdelossantos"
        date_str = (
            uploaded_text.text.strip().split("\n")[0].strip() if uploaded_text else None
        )
        uploaded = pd.to_datetime(date_str, errors="coerce") if date_str else None

        platform_text = entry.select_one(
            "span.list-col-subtitle:-soup-contains('Platform') + span"
        )
        platform = platform_text.text.strip() if platform_text else None
        single_core_score = entry.select_one(
            "span.list-col-subtitle-score:-soup-contains('Single-Core Score') + span"
        )
        multi_core_score = entry.select_one(
            "span.list-col-subtitle-score:-soup-contains('Multi-Core Score') + span"
        )

        # Convert scores to integers using isdigit()
        single_score = None
        if single_core_score:
            score_text = single_core_score.text.strip().replace(",", "")
            single_score = int(score_text) if score_text.isdigit() else None

        multi_score = None
        if multi_core_score:
            score_text = multi_core_score.text.strip().replace(",", "")
            multi_score = int(score_text) if score_text.isdigit() else None

        return GeekbenchProcessorResult(
            cpu_id=url.split("/")[-1],
            system=system,
            cpu_model=cpu_model,
            frequency=cpu_freq,
            cores=cpu_cores,
            uploaded=uploaded,
            platform=platform,
            single_core_score=single_score,
            multi_core_score=multi_score,
            url=url,
        )

    def get_total_pages(self) -> int:
        """Get the total number of pages available for the CPU."""
        if self._total_pages is not None:
            return self._total_pages

        response = requests.get(
            self._get_base_url(), headers=HEADERS, params=self._get_params(1)
        )
        soup = BeautifulSoup(response.text, "html.parser")

        # Find pagination info
        pagination = soup.select_one("ul.pagination")
        if not pagination:
            self._total_pages = 1
            return self._total_pages

        # Get the last page number from pagination
        page_links = pagination.select("li.page-item a.page-link")
        if not page_links:
            self._total_pages = 1
            return self._total_pages

        try:
            self._total_pages = max(
                int(link.text.strip())
                for link in page_links
                if link.text.strip().isdigit()
            )
        except ValueError:
            self._total_pages = 1

        if (self.max_pages is not None) and (self.max_pages > 0):
            print(
                f"Total pages detected: {self._total_pages}; Limit = {self.max_pages}",
            )
            self._total_pages = min(self._total_pages, self.max_pages)

        return self._total_pages

    def scrape_page(self, page: int) -> list[GeekbenchProcessorResult]:
        """Scrape a single page of results."""
        response = requests.get(
            self._get_base_url(),
            headers=HEADERS,
            params=self._get_params(page),
        )
        soup = BeautifulSoup(response.text, "html.parser")
        result_div = soup.select('div[class="row"] div[class="col-12 col-lg-9"] div')[1]
        entries = result_div.select('div[class="col-12 list-col"]')

        return [self._parse_entry(entry) for entry in entries]

    def scrape_multiple_pages(
        self, start_page: int = 1, end_page: int | None = None
    ) -> pd.DataFrame:
        """
        Scrape multiple pages of results.

        Args:
            start_page: The page number to start scraping from (default: 1)
            end_page: The page number to end scraping at (default: None, will scrape all pages)

        Returns:
            DataFrame containing all scraped results
        """
        if end_page is None:
            end_page = self.get_total_pages()

        if start_page < 1:
            start_page = 1
        if end_page > self.get_total_pages():
            end_page = self.get_total_pages()

        all_results = []
        for page in range(start_page, end_page + 1):
            results = self.scrape_page(page)
            all_results.extend(results)

        return pd.DataFrame([vars(result) for result in all_results])


# Example usage
if __name__ == "__main__":
    import time

    proc_name_list = [
        "AMD Ryzen 9 9950X3D",
        # "AMD Ryzen 9 7940HS",
        # "Intel Core i7-12700F",
        # "Intel Core i7-12700",
    ]

    start_time = time.time()

    for proc_name in proc_name_list:
        start_time = time.time()

        print(f"Processing {proc_name}")

        scraper = GeekbenchProcessorResultScraper(proc_name, max_pages=30)
        total_pages = scraper.get_total_pages()

        print(f"Total pages available: {total_pages}")

        df = scraper.scrape_multiple_pages()
        df.to_csv(f"{proc_name.replace(' ', '_')}.csv", index=False)

        print(f"Total results found: {len(df)}")
        print(f"{time.time() - start_time} seconds took.")
        print("==========")
