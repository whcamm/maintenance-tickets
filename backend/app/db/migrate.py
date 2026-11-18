import logging
import time
from pathlib import Path

import pymysql

from app.core.config import get_settings
from app.core.database import connect

logger = logging.getLogger(__name__)

DEFAULT_DELIMITER = ";"


def split_statements(script: str) -> list[str]:
    statements: list[str] = []
    delimiter = DEFAULT_DELIMITER
    buffer: list[str] = []

    for line in script.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(maxsplit=1)[1]
            continue
        if not buffer and (not stripped or stripped.startswith("--")):
            continue
        buffer.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(buffer).rstrip()
            statements.append(statement[: -len(delimiter)].strip())
            buffer = []

    if "".join(buffer).strip():
        statements.append("\n".join(buffer).strip())
    return statements


def run_script(connection: pymysql.connections.Connection, path: Path) -> None:
    with connection.cursor() as cursor:
        for statement in split_statements(path.read_text(encoding="utf-8")):
            cursor.execute(statement)
            while cursor.nextset():
                pass


def connect_with_retry(attempts: int = 10, delay_seconds: float = 3.0) -> pymysql.connections.Connection:
    database = get_settings().database
    for attempt in range(1, attempts + 1):
        try:
            return connect(database)
        except pymysql.err.OperationalError:
            if attempt == attempts:
                raise
            logger.warning("Database not ready (attempt %s/%s), retrying...", attempt, attempts)
            time.sleep(delay_seconds)
    raise RuntimeError("Unreachable")


def migrate() -> None:
    scripts = sorted(get_settings().db_scripts_dir.glob("*.sql"))
    if not scripts:
        raise FileNotFoundError(f"No SQL scripts found in {get_settings().db_scripts_dir}")

    connection = connect_with_retry()
    try:
        for script in scripts:
            logger.info("Applying %s", script.name)
            run_script(connection, script)
    finally:
        connection.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
    migrate()
