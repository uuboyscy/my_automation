"""Connection for databases."""

from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Connection


def get_postgresql_conn(
    database: str,
    user: str,
    password: str,
    host: str,
    port: int = 5432,
    connect_args: dict | None = None,
) -> Connection:
    """Get PostgreSQL connection."""
    user = quote_plus(user)
    password = quote_plus(password)

    # PostgreSQL-specific connect arguments
    default_connect_args = {"sslmode": "prefer"}  # add any other necessary arguments
    connect_args = (
        connect_args | default_connect_args if connect_args else default_connect_args
    )

    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}",
        connect_args=connect_args,
    ).connect()


# Example usage. Don't execute this file directly
if __name__ == "__main__":
    import pandas as pd

    conn = get_postgresql_conn(
        database="database", user="user", password="password", host="host"
    )

    df = pd.read_sql("select * from organization", conn)
