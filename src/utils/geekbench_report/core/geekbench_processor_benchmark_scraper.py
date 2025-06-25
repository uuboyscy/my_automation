import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://browser.geekbench.com/processor-benchmarks"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}


@dataclass
class GeekbenchProcessorBenchmark:
    cpu_model: str
    frequency: str | None
    cores: int | None
    single_core_score: int | None
    multi_core_score: int | None


def parse_processor_row(row):
    name_cell = row.select_one("td.name a")
    cpu_model = name_cell.text.strip() if name_cell else None
    freq_cores_text = (
        row.select_one("td.name").text.replace(cpu_model, "").strip()
        if name_cell
        else ""
    )
    freq_match = re.search(r"([\d.]+\s*GHz)", freq_cores_text)
    freq = freq_match.group(1) if freq_match else None
    cores_match = re.search(r"\((\d+) cores?\)", freq_cores_text)
    cores = int(cores_match.group(1)) if cores_match else None
    score_cells = row.select("td.score")
    score = (
        int(score_cells[0].text.strip().replace(",", ""))
        if len(score_cells) > 0
        else None
    )
    return {
        "cpu_model": cpu_model,
        "frequency": freq,
        "cores": cores,
        "score": score,
    }


def extract_processor_rows_from_div(soup, div_id):
    """
    Extract all processor rows from the table under the specified div_id.
    Returns a dict with processor name as key.
    """
    div = soup.find("div", id=div_id)
    if not div:
        return {}
    table = div.select_one("table.table")
    rows = table.select("tbody tr") if table else []
    result = {}
    for row in rows:
        data = parse_processor_row(row)
        if data["cpu_model"]:
            result[data["cpu_model"]] = data
    return result


def scrape_page() -> list[GeekbenchProcessorBenchmark]:
    """
    Scrape single-core and multi-core data separately and merge by processor name.
    Returns:
        list of GeekbenchProcessorBenchmark
    """
    response = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    single_core_dict = extract_processor_rows_from_div(soup, "single-core")
    multi_core_dict = extract_processor_rows_from_div(soup, "multi-core")

    all_names = set(single_core_dict.keys()) | set(multi_core_dict.keys())
    result_list = []
    for name in all_names:
        single = single_core_dict.get(name)
        multi = multi_core_dict.get(name)
        benchmark = GeekbenchProcessorBenchmark(
            cpu_model=name,
            frequency=(
                single["frequency"]
                if single
                else (multi["frequency"] if multi else None)
            ),
            cores=single["cores"] if single else (multi["cores"] if multi else None),
            single_core_score=single["score"] if single else None,
            multi_core_score=multi["score"] if multi else None,
        )
        result_list.append(benchmark)
    return result_list


if __name__ == "__main__":
    import json
    from dataclasses import asdict

    print(json.dumps([asdict(x) for x in scrape_page()], indent=2, ensure_ascii=False))
