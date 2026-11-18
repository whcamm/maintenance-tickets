from collections.abc import Sequence
from typing import Any

import pymysql

from app.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
)

ERROR_BY_MYSQL_ERRNO = {
    5404: NotFoundError,
    5409: InvalidTransitionError,
    5410: ConflictError,
    5422: BusinessRuleViolationError,
}


def call_procedure(
    connection: pymysql.connections.Connection, name: str, args: Sequence[Any]
) -> list[dict[str, Any]]:
    placeholders = ", ".join(["%s"] * len(args))
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CALL {name}({placeholders})", tuple(args))
            rows = list(cursor.fetchall())
            while cursor.nextset():
                pass
            return rows
    except pymysql.err.MySQLError as exc:
        errno = exc.args[0] if exc.args else None
        domain_error = ERROR_BY_MYSQL_ERRNO.get(errno)
        if domain_error is not None:
            raise domain_error(str(exc.args[1])) from exc
        raise
