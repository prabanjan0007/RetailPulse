from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from retailpulse.config import settings


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """Yield a database connection and always close it afterwards."""
    with psycopg.connect(settings.database_url, row_factory=dict_row) as connection:
        yield connection


def initialize_schema() -> None:
    schema_path = Path(__file__).parents[1] / "sql" / "schema.sql"
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(schema_path.read_text(encoding="utf-8"))
        connection.commit()
