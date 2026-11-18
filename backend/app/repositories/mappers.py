from datetime import UTC, datetime
from typing import Any

from app.domain.models import HistoryEntry, HistoryEventType, Notification, Operator, Ticket
from app.domain.workflow import TicketStatus


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def optional_status(value: str | None) -> TicketStatus | None:
    return TicketStatus(value) if value else None


def to_ticket(row: dict[str, Any]) -> Ticket:
    return Ticket(
        id=row["id"],
        title=row["title"],
        asset_code=row["asset_code"],
        description=row["description"],
        status=TicketStatus(row["status"]),
        diagnosis=row["diagnosis"],
        reported_by=row["reported_by"],
        assigned_operator_id=row["assigned_operator_id"],
        assigned_operator_name=row["assigned_operator_name"],
        created_at=as_utc(row["created_at"]),
        updated_at=as_utc(row["updated_at"]),
    )


def to_history_entry(row: dict[str, Any]) -> HistoryEntry:
    return HistoryEntry(
        id=row["id"],
        ticket_id=row["ticket_id"],
        event_type=HistoryEventType(row["event_type"]),
        from_status=optional_status(row["from_status"]),
        to_status=optional_status(row["to_status"]),
        comment=row["comment"],
        actor=row["actor"],
        created_at=as_utc(row["created_at"]),
    )


def to_operator(row: dict[str, Any]) -> Operator:
    return Operator(id=row["id"], full_name=row["full_name"], email=row["email"])


def to_notification(row: dict[str, Any]) -> Notification:
    return Notification(
        id=row["id"],
        ticket_id=row["ticket_id"],
        recipient=row["recipient"],
        channel=row["channel"],
        message=row["message"],
        created_at=as_utc(row["created_at"]),
    )
