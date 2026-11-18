import pymysql

from app.domain.models import Operator
from app.repositories.mappers import to_operator


class MySqlOperatorRepository:
    def __init__(self, connection: pymysql.connections.Connection) -> None:
        self._connection = connection

    def find_all(self) -> list[Operator]:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id, full_name, email FROM operators ORDER BY full_name")
            rows = cursor.fetchall()
        return [to_operator(row) for row in rows]

    def get(self, operator_id: int) -> Operator | None:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT id, full_name, email FROM operators WHERE id = %s", (operator_id,))
            row = cursor.fetchone()
        return to_operator(row) if row else None
