BASE_URL = "https://browser.geekbench.com/v6/cpu"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}


class GeekbenchProcessorNameScraper:
    def __init__(self, cpu_name: str) -> None:
        self.cpu_name = cpu_name

    def scrape_page(self, page: int) -> list[str]:
        pass

    def scrape_multiple_pages(
        self, start_page: int = 1, end_page: int | None = None
    ) -> list[str]:
        pass
