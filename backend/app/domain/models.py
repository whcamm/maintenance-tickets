from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from app.domain.workflow import TicketStatus


class HistoryEventType(StrEnum):
    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    COMMENT = "COMMENT"
    ASSIGNED = "ASSIGNED"


@dataclass(frozen=True)
class Operator:
    id: int
    full_name: str
    email: str


@dataclass(frozen=True)
class Ticket:
    id: int
    title: str
    asset_code: str
    description: str | None
    status: TicketStatus
    diagnosis: str | None
    reported_by: str
    assigned_operator_id: int | None
    assigned_operator_name: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class HistoryEntry:
    id: int
    ticket_id: int
    event_type: HistoryEventType
    from_status: TicketStatus | None
    to_status: TicketStatus | None
    comment: str | None
    actor: str
    created_at: datetime


@dataclass(frozen=True)
class Notification:
    id: int
    ticket_id: int
    recipient: str
    channel: str
    message: str
    created_at: datetime


@dataclass(frozen=True)
class NewTicket:
    title: str
    asset_code: str
    description: str | None
    reported_by: str
    assigned_operator_id: int | None = None


@dataclass(frozen=True)
class TicketFilters:
    status: TicketStatus | None = None
    operator_id: int | None = None
    created_from: date | None = None
    created_to: date | None = None
