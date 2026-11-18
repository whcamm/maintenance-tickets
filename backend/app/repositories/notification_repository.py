import pymysql

from app.domain.models import Notification
from app.repositories.mappers import to_notification


class MySqlNotificationRepository:
    def __init__(self, connection: pymysql.connections.Connection) -> None:
        self._connection = connection

    def save(self, ticket_id: int, history_id: int, recipient: str, message: str) -> int:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notifications (ticket_id, history_id, recipient, message) VALUES (%s, %s, %s, %s)",
                (ticket_id, history_id, recipient, message),
            )
            return int(cursor.lastrowid)

    def recent(self, limit: int) -> list[Notification]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, ticket_id, recipient, channel, message, created_at "
                "FROM notifications ORDER BY created_at DESC, id DESC LIMIT %s",
                (limit,),
            )
            rows = cursor.fetchall()
        return [to_notification(row) for row in rows]
