# Geekbench Report

This subproject scrapes CPU performance data from [Geekbench Browser](https://browser.geekbench.com/) and loads the
results into a PostgreSQL database.  It is designed as a simple data pipeline
exercise and can be used in a data engineering course.

## Directory overview

```
src/app/geekbench_report/       # Entry scripts that orchestrate the ETL steps
src/utils/geekbench_report/     # Scraper classes and database helpers
src/utils/common/               # Generic utilities (e.g., database connection)
```

### Entry scripts

- **sync_cpu_model_name_to_pg.py** – crawls recent results and benchmark pages
to collect distinct CPU names and stores them in `cpu_model_names`.
- **sync_cpu_model_benchmark_to_pg.py** – scrapes the benchmark page to get
single/multi‑core scores for common processors and saves them to
`cpu_model_benchmarks`.
- **sync_cpu_model_result_to_pg.py** – downloads result listings for each CPU
model, updating the `cpu_model_results` table.  It keeps track of already synced
records using timestamps and removes duplicates.
- **sync_cpu_model_detail_to_pg.py** – fetches full details for individual
results and stores them in `cpu_model_details`.

The scripts rely on helper functions located under
`src/utils/geekbench_report/`:

- `core/` – web scrapers implemented with `requests` and `BeautifulSoup`.
- `database_helper.py` – functions to insert pandas DataFrames into PostgreSQL
and to look up IDs or delete duplicate records.

## Configuring the database

The following environment variables are read by `database_helper.py`:

- `GEEKBENCH_REPORT_POSTGRESDB_SCHEMA`
- `GEEKBENCH_REPORT_POSTGRESDB_HOST`
- `GEEKBENCH_REPORT_POSTGRESDB_DATABASE`
- `GEEKBENCH_REPORT_POSTGRESDB_PORT`
- `GEEKBENCH_REPORT_POSTGRESDB_USER`
- `GEEKBENCH_REPORT_POSTGRESDB_PASSWORD`

Set these variables before running any sync script so that the scripts can
connect to your PostgreSQL instance.

## Installing dependencies

The project uses Python 3.12 and depends on packages listed in
`requirements.txt` (or `pyproject.toml`).  Install them with:

```bash
pip install -r requirements.txt
```

## Typical workflow

1. **Update CPU names** – run `sync_cpu_model_name_to_pg.py` to populate the
   `cpu_model_names` table.
2. **Collect benchmark summaries** – run `sync_cpu_model_benchmark_to_pg.py` to
   store frequency, core count and scores for each model.
3. **Load result listings** – run `sync_cpu_model_result_to_pg.py` to fetch all
   individual result pages.  This script can resume from an offset if interrupted.
4. **Fetch detailed results** – run `sync_cpu_model_detail_to_pg.py` to enrich
   each CPU model with system information and benchmark breakdowns.

Each step writes a pandas DataFrame directly into PostgreSQL via SQLAlchemy.

For an overview of the tables created by these scripts see
[SCHEMA.md](SCHEMA.md).

Teaching suggestions and additional learning notes are provided in
[EDUCATION.md](EDUCATION.md).
