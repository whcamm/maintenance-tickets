from collections.abc import Iterator

import pymysql
from pymysql.cursors import DictCursor

from app.core.config import DatabaseSettings, get_settings


def connect(database: DatabaseSettings) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=database.host,
        port=database.port,
        user=database.user,
        password=database.password,
        database=database.name,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=10,
        init_command="SET time_zone = '+00:00'",
    )


def get_connection() -> Iterator[pymysql.connections.Connection]:
    connection = connect(get_settings().database)
    try:
        yield connection
    finally:
        connection.close()
