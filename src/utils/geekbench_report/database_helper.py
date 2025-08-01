import os
from datetime import datetime
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

from utils.common.database_utility import get_postgresql_conn

load_dotenv()

GEEKBENCH_REPORT_POSTGRESDB_SCHEMA = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_SCHEMA")
GEEKBENCH_REPORT_POSTGRESDB_HOST = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_HOST")
GEEKBENCH_REPORT_POSTGRESDB_DATABASE = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_DATABASE")
GEEKBENCH_REPORT_POSTGRESDB_PORT = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_PORT")
GEEKBENCH_REPORT_POSTGRESDB_USER = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_USER")
GEEKBENCH_REPORT_POSTGRESDB_PASSWORD = os.getenv("GEEKBENCH_REPORT_POSTGRESDB_PASSWORD")


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


def update_cpu_model_names(check_update_list: list[str]) -> None:
    """Sync CPU model names to PostgreSQL database."""
    df = pd.DataFrame(check_update_list, columns=["cpu_model"])

    # Read existing CPU model names from database
    existing_model_list = get_cpu_model_name_list_from_pg()
    existing_model_set = set(existing_model_list)

    # Find new CPU models that need to be added
    new_models = set(df["cpu_model"]) - existing_model_set
    if new_models:
        new_df = pd.DataFrame(list(new_models), columns=["cpu_model"])
        load_df_to_pg(
            df=new_df,
            table_name="cpu_model_names",
            if_exists="append",
        )
        print(f"Added {len(new_models)} new CPU models to database")
        print(new_models)
    else:
        print("No new CPU models to add")


def update_system_names(check_update_list: list[str]) -> None:
    """Sync system names to PostgreSQL database."""
    df = pd.DataFrame(check_update_list, columns=["system"])

    # Read existing records from database
    existing_system_list = get_system_name_list_from_pg()
    existing_system_set = set(existing_system_list)

    # Find new systems that need to be added
    new_systems = set(df["system"]) - existing_system_set
    if new_systems:
        new_df = pd.DataFrame(list(new_systems), columns=["system"])
        load_df_to_pg(
            df=new_df,
            table_name="system_names",
            if_exists="append",
        )
        print(f"Added {len(new_systems)} new systems to database")
        print(new_systems)
    else:
        print("No new systems to add")


def get_last_updated_dates_of_cpu_model_df() -> pd.DataFrame:
    sql = """
        with last_uploaded_record as (
            select
                cpu_model_id
                , max(uploaded) as last_uploaded
            from cpu_model_results
            group by cpu_model_id
        )
        select
            d.cpu_model
            , COALESCE(f.last_uploaded, CURRENT_DATE - INTERVAL '30 days') AS last_uploaded
        from cpu_model_names d
        left join last_uploaded_record f
        on d.cpu_model_id = f.cpu_model_id
        where d.cpu_model <> 'ARM'
        order by d.cpu_model_id
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        return pd.read_sql(sql, conn)


def get_cpu_model_id_and_result_id_for_scraping_details_df() -> pd.DataFrame:
    """
    This function used only for getting cpu_codename as dimension from detail URL.
    So it will not scrape for all result_id.
    Only one random result_id of a cpu_model_id will be scraped.
    """
    sql = """
        with cpu_model_id_with_result_id as (
            select
                cpu_model_id,
                max(cpu_result_id) as cpu_result_id
            from cpu_model_results
            group by cpu_model_id
        )
        select
            cpu_model_id,
            cpu_result_id
        from cpu_model_id_with_result_id
        where cpu_model_id not in (
            select cpu_model_id from cpu_model_details
        )
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        return pd.read_sql(sql, conn)


def delete_cpu_model_result_record_from_date_to_now(
    cpu_model: str,
    from_date: str | datetime,
) -> None:
    from_date = pd.to_datetime(from_date)
    delete_sql = f"""
        delete from cpu_model_results
        where cpu_model_id = (
            select cpu_model_id from cpu_model_names where cpu_model = '{cpu_model}'
        )
        and uploaded >= '{from_date}'
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        print(
            f"Deleting cpu_model='{cpu_model}'/uploaded>='{from_date}' from cpu_model_results..."
        )
        print(conn.execute(text(delete_sql)), "affected.")
        conn.commit()


def delete_duplicated_cpu_model_result_from_pg() -> None:
    delete_sql = """
        with ranked as (
        select ctid,
                ROW_NUMBER() OVER (
                partition by cpu_result_id, system_id, cpu_model_id, frequency, cores,
                                uploaded, platform, single_core_score, multi_core_score
                order by ctid
                ) as rn
        from cpu_model_results
        )
        delete from cpu_model_results
        where ctid in (
        select ctid
        from ranked
        where rn > 1
        )
    """
    with get_postgresql_conn(
        database=GEEKBENCH_REPORT_POSTGRESDB_DATABASE,
        user=GEEKBENCH_REPORT_POSTGRESDB_USER,
        password=GEEKBENCH_REPORT_POSTGRESDB_PASSWORD,
        host=GEEKBENCH_REPORT_POSTGRESDB_HOST,
        port=GEEKBENCH_REPORT_POSTGRESDB_PORT,
    ) as conn:
        print("Deleting duplicated data from cpu_model_results...")
        print(conn.execute(text(delete_sql)), "affected.")
        conn.commit()
