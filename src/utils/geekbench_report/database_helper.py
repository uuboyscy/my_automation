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


def get_cpu_model_name_list_from_pg() -> list[str]:
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        sql = "select cpu_model FROM cpu_model_names"
        return pd.read_sql(
            sql,
            conn,
        )["cpu_model"].to_list()


def get_system_name_list_from_pg() -> list[str]:
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        sql = "select system FROM system_names"
        return pd.read_sql(
            sql,
            conn,
        )["system"].to_list()


def get_cpu_model_map_from_pg() -> dict[str, int]:
    """
    Return a dict with key as cpu_model and value as cpu_model_id.
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        sql = "select cpu_model, cpu_model_id FROM cpu_model_names"
        df = pd.read_sql(sql, conn)
        return dict(zip(df["cpu_model"], df["cpu_model_id"]))


def get_system_map_from_pg() -> dict[str, int]:
    """
    Return a dict with key as system and value as system_id.
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        sql = "select system, system_id FROM system_names"
        df = pd.read_sql(sql, conn)
        return dict(zip(df["system"], df["system_id"]))


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


def get_sorted_detail_url_list() -> list[str]:
    # The `where row_number = 1` will be removed after there exists at least on record for each CPU model
    sql = """
        select url
        from (
            select
                cpu_model,
                url,
                ROW_NUMBER() OVER (PARTITION BY cpu_model ORDER BY url ASC) AS row_number
            from cpu_model_results
        ) AS ranked
        where row_number = 1
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        return pd.read_sql(sql, conn)["url"].to_list()


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
