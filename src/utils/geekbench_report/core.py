from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup


@dataclass
class GeekbenchResult:
    system: Optional[str]
    cpu_model: Optional[str]
    frequency: Optional[str]
    cores: Optional[str]
    uploaded: Optional[str]
    platform: Optional[str]
    single_core_score: Optional[str]
    multi_core_score: Optional[str]
    url: Optional[str]


class GeekbenchScraper:
    BASE_URL = "https://browser.geekbench.com/search"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    def __init__(self, cpu_name: str):
        self.cpu_name = cpu_name
        self._total_pages = None

    def _get_page_url(self, page: int) -> str:
        return self.BASE_URL

    def _get_params(self, page: int) -> Dict[str, str]:
        return {"q": self.cpu_name, "page": str(page)}

    def _parse_entry(self, entry) -> GeekbenchResult:
        system_a = entry.select_one("a[href^='/v6/cpu/']")
        system = system_a.text.strip() if system_a else None
        url = system_a["href"] if system_a and system_a.has_attr("href") else None

        cpu_info = entry.select_one("span.list-col-model")
        cpu_lines = cpu_info.text.strip().split("\n") if cpu_info else []
        cpu_model = cpu_lines[0].strip() if len(cpu_lines) > 0 else None
        cpu_freq = cpu_lines[1].strip() if len(cpu_lines) > 1 else None
        cpu_cores = cpu_lines[2].strip("() \n") if len(cpu_lines) > 2 else None

        uploaded_text = entry.select_one(
            "span.list-col-subtitle:contains('Uploaded') + span"
        )
        platform_text = entry.select_one(
            "span.list-col-subtitle:contains('Platform') + span"
        )
        single_core_score = entry.select_one(
            "span.list-col-subtitle-score:contains('Single-Core Score') + span"
        )
        multi_core_score = entry.select_one(
            "span.list-col-subtitle-score:contains('Multi-Core Score') + span"
        )

        return GeekbenchResult(
            system=system,
            cpu_model=cpu_model,
            frequency=cpu_freq,
            cores=cpu_cores,
            uploaded=uploaded_text.text.strip() if uploaded_text else None,
            platform=platform_text.text.strip() if platform_text else None,
            single_core_score=(
                single_core_score.text.strip() if single_core_score else None
            ),
            multi_core_score=(
                multi_core_score.text.strip() if multi_core_score else None
            ),
            url=f"https://browser.geekbench.com{url}" if url else None,
        )

    def get_total_pages(self) -> int:
        """Get the total number of pages available for the CPU."""
        if self._total_pages is not None:
            return self._total_pages

        response = requests.get(
            self._get_page_url(1), headers=self.HEADERS, params=self._get_params(1)
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

        return self._total_pages

    def scrape_page(self, page: int) -> List[GeekbenchResult]:
        """Scrape a single page of results."""
        response = requests.get(
            self._get_page_url(page),
            headers=self.HEADERS,
            params=self._get_params(page),
        )
        soup = BeautifulSoup(response.text, "html.parser")
        result_div = soup.select('div[class="row"] div[class="col-12 col-lg-9"] div')[1]
        entries = result_div.select('div[class="col-12 list-col"]')

        return [self._parse_entry(entry) for entry in entries]

    def scrape_multiple_pages(
        self, start_page: int = 1, end_page: Optional[int] = None
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
    scraper = GeekbenchScraper("AMD Ryzen 9 9950X3D")
    total_pages = scraper.get_total_pages()

    print(f"Total pages available: {total_pages}")

    # Scrape all pages
    df = scraper.scrape_multiple_pages()
    df.to_csv("test_geekbench_results.csv", index=False)
    print(f"Total results found: {len(df)}")
