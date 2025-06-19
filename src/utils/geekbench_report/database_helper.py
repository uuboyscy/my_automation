import os
from typing import Literal

import pandas as pd
from dotenv import load_dotenv

from utils.common.database_utility import get_postgresql_conn

load_dotenv()

GEEKBENCH_REPORT_POSTGRESDB_SCHEMA = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_SCHEMA")
GEEKBENCH_REPORT_POSTGRESDB_HOST = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_HOST")
GEEKBENCH_REPORT_POSTGRESDB_DATABASE = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_DATABASE")
GEEKBENCH_REPORT_POSTGRESDB_PORT = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_PORT")
GEEKBENCH_REPORT_POSTGRESDB_USER = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_USER")
GEEKBENCH_REPORT_POSTGRESDB_PASSWORD = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_PASSWORD")


def get_cpu_model_name_list_from_pg(limit: int | None = None) -> list[str]:
    if not limit:
        limit = 1

    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        sql = "select cpu_model FROM cpu_model_names"

        if limit is not None:
            sql += f" limit {limit}"

        return pd.read_sql(
            sql,
            conn,
        )["cpu_model"].to_list()


def get_last_updated_dates_of_cpu_model_df() -> pd.DataFrame:
    sql = """
        select
            cpu_model
            , max(uploaded) as last_uploaded
        from cpu_model_results
        group by cpu_model
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        return pd.read_sql(sql, conn)


def load_df_to_pg(
    df: pd.DataFrame,
    table_name: str,
    if_exists: Literal["fail", "replace", "append"] = "fail",
) -> None:
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        df.to_sql(
            table_name,
            conn,
            if_exists=if_exists,
            index=False,
        )
