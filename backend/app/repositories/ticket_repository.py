from datetime import timedelta
from typing import Any

import pymysql

from app.domain.models import HistoryEntry, NewTicket, Ticket, TicketFilters
from app.domain.workflow import TicketStatus
from app.repositories.mappers import to_history_entry, to_ticket
from app.repositories.procedures import call_procedure

TICKET_SELECT = """
    SELECT t.id, t.title, t.asset_code, t.description, t.status, t.diagnosis, t.reported_by,
           t.assigned_operator_id, o.full_name AS assigned_operator_name, t.created_at, t.updated_at
    FROM tickets t
    LEFT JOIN operators o ON o.id = t.assigned_operator_id
"""

HISTORY_SELECT = """
    SELECT id, ticket_id, event_type, from_status, to_status, comment, actor, created_at
    FROM ticket_history
"""


class MySqlTicketRepository:
    def __init__(self, connection: pymysql.connections.Connection) -> None:
        self._connection = connection

    def create(self, new_ticket: NewTicket) -> int:
        rows = call_procedure(
            self._connection,
            "sp_create_ticket",
            [
                new_ticket.title,
                new_ticket.asset_code,
                new_ticket.description,
                new_ticket.reported_by,
                new_ticket.assigned_operator_id,
            ],
        )
        return int(rows[0]["ticket_id"])

    def get(self, ticket_id: int) -> Ticket | None:
        with self._connection.cursor() as cursor:
            cursor.execute(TICKET_SELECT + " WHERE t.id = %s", (ticket_id,))
            row = cursor.fetchone()
        return to_ticket(row) if row else None

    def search(self, filters: TicketFilters) -> list[Ticket]:
        conditions: list[str] = []
        params: list[Any] = []

        if filters.status is not None:
            conditions.append("t.status = %s")
            params.append(filters.status.value)
        if filters.operator_id is not None:
            conditions.append("t.assigned_operator_id = %s")
            params.append(filters.operator_id)
        if filters.created_from is not None:
            conditions.append("t.created_at >= %s")
            params.append(filters.created_from)
        if filters.created_to is not None:
            conditions.append("t.created_at < %s")
            params.append(filters.created_to + timedelta(days=1))

        query = TICKET_SELECT
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY t.created_at DESC, t.id DESC"

        with self._connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        return [to_ticket(row) for row in rows]

    def transition(
        self,
        ticket_id: int,
        target: TicketStatus,
        diagnosis: str | None,
        comment: str | None,
        actor: str,
    ) -> int:
        rows = call_procedure(
            self._connection,
            "sp_transition_ticket_status",
            [ticket_id, target.value, diagnosis, comment, actor],
        )
        return int(rows[0]["history_id"])

    def add_comment(self, ticket_id: int, comment: str, actor: str) -> int:
        rows = call_procedure(self._connection, "sp_add_ticket_comment", [ticket_id, comment, actor])
        return int(rows[0]["history_id"])

    def assign(self, ticket_id: int, operator_id: int, actor: str) -> int:
        rows = call_procedure(self._connection, "sp_assign_ticket", [ticket_id, operator_id, actor])
        return int(rows[0]["history_id"])

    def history(self, ticket_id: int) -> list[HistoryEntry]:
        with self._connection.cursor() as cursor:
            cursor.execute(HISTORY_SELECT + " WHERE ticket_id = %s ORDER BY created_at, id", (ticket_id,))
            rows = cursor.fetchall()
        return [to_history_entry(row) for row in rows]

    def history_entry(self, history_id: int) -> HistoryEntry | None:
        with self._connection.cursor() as cursor:
            cursor.execute(HISTORY_SELECT + " WHERE id = %s", (history_id,))
            row = cursor.fetchone()
        return to_history_entry(row) if row else None
