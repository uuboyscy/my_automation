from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://browser.geekbench.com/v6/cpu/{cpu_id}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}


@dataclass
class GeekbenchProcessorDetail:
    title: str | None
    upload_date: str | None
    views: str | None
    single_core_score: str | None
    multi_core_score: str | None
    system_info: dict[str, str]
    cpu_info: dict[str, str]
    memory_info: dict[str, str]
    single_core_benchmarks: dict[str, dict[str, str]]
    multi_core_benchmarks: dict[str, dict[str, str]]


class GeekbenchProcessorDetailScraper:
    def __init__(self, cpu_id: str) -> None:
        self.cpu_id = cpu_id

    def _get_detail_url(self) -> str:
        return BASE_URL.format(cpu_id=self.cpu_id)

    def _parse_table(self, soup, index: int) -> dict[str, str]:
        """Extract a key-value table based on class 'system-table' by index."""
        data = {}
        rows = soup.select("table.system-table")[index].select("tbody tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                data[key] = value
        return data

    def _parse_benchmark_table(self, table) -> dict[str, dict[str, str]]:
        benchmarks = {}
        for row in table.select("tbody tr"):
            name_tag = row.find("td", class_="name")
            score_tag = row.find("td", class_="score")
            desc_tag = row.find("span", class_="description")
            if name_tag and score_tag:
                name = name_tag.get_text(strip=True)
                score = score_tag.contents[0].strip()
                description = desc_tag.get_text(strip=True) if desc_tag else ""
                benchmarks[name] = {"score": score, "description": description}
        return benchmarks

    def scrape_detail_page(self) -> GeekbenchProcessorDetail:
        response = requests.get(self._get_detail_url(), headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = soup.title.string.strip() if soup.title else None

        # Extract scores
        score_tags = soup.select(".score-container .score")
        single_core_score = score_tags[0].text.strip() if len(score_tags) > 0 else None
        multi_core_score = score_tags[1].text.strip() if len(score_tags) > 1 else None

        # Upload date and views
        def get_value(label: str) -> str | None:
            td = soup.find("td", class_="system-name", string=label)
            return td.find_next_sibling("td").get_text(strip=True) if td else None

        upload_date = get_value("Upload Date")
        views = get_value("Views")

        # System / CPU / Memory tables (by known indexes)
        system_info = self._parse_table(soup, 1)
        cpu_info = self._parse_table(soup, 2)
        memory_info = self._parse_table(soup, 3)

        # Benchmarks
        benchmark_tables = soup.select("table.benchmark-table")
        single_core_benchmarks = (
            self._parse_benchmark_table(benchmark_tables[0])
            if len(benchmark_tables) > 0
            else {}
        )
        multi_core_benchmarks = (
            self._parse_benchmark_table(benchmark_tables[1])
            if len(benchmark_tables) > 1
            else {}
        )

        return GeekbenchProcessorDetail(
            title=title,
            upload_date=upload_date,
            views=views,
            single_core_score=single_core_score,
            multi_core_score=multi_core_score,
            system_info=system_info,
            cpu_info=cpu_info,
            memory_info=memory_info,
            single_core_benchmarks=single_core_benchmarks,
            multi_core_benchmarks=multi_core_benchmarks,
        )


# Example usage:
if __name__ == "__main__":
    from pprint import pprint

    scraper = GeekbenchProcessorDetailScraper("12479005")
    result = scraper.scrape_detail_page()
    pprint(result)  # To convert to JSON-serializable dictionary
