from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import HistoryEntry, HistoryEventType, Notification, Operator, Ticket
from app.domain.workflow import TicketStatus, TransitionRule


class RequestModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class TicketCreateRequest(RequestModel):
    title: str = Field(min_length=3, max_length=120, examples=["ATM out of service"])
    asset_code: str = Field(min_length=2, max_length=30, pattern=r"^[A-Za-z0-9-]+$", examples=["ATM-0451"])
    description: str | None = Field(default=None, max_length=2000, examples=["Screen does not respond."])
    reported_by: str = Field(min_length=2, max_length=100, examples=["Branch manager"])
    assigned_operator_id: int | None = Field(default=None, gt=0)


class StatusTransitionRequest(RequestModel):
    to_status: TicketStatus
    actor: str = Field(min_length=2, max_length=100)
    diagnosis: str | None = Field(default=None, max_length=2000)
    comment: str | None = Field(default=None, max_length=2000)


class CommentCreateRequest(RequestModel):
    comment: str = Field(min_length=1, max_length=2000)
    actor: str = Field(min_length=2, max_length=100)


class AssignmentRequest(RequestModel):
    operator_id: int = Field(gt=0)
    actor: str = Field(min_length=2, max_length=100)


class TransitionResponse(BaseModel):
    from_status: TicketStatus
    to_status: TicketStatus
    requires_diagnosis: bool
    requires_comment: bool

    @classmethod
    def from_rule(cls, rule: TransitionRule) -> "TransitionResponse":
        return cls(
            from_status=rule.source,
            to_status=rule.target,
            requires_diagnosis=rule.requires_diagnosis,
            requires_comment=rule.requires_comment,
        )


class TicketResponse(BaseModel):
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
    allowed_transitions: list[TransitionResponse]

    @classmethod
    def from_domain(cls, ticket: Ticket, transitions: list[TransitionRule]) -> "TicketResponse":
        return cls(
            id=ticket.id,
            title=ticket.title,
            asset_code=ticket.asset_code,
            description=ticket.description,
            status=ticket.status,
            diagnosis=ticket.diagnosis,
            reported_by=ticket.reported_by,
            assigned_operator_id=ticket.assigned_operator_id,
            assigned_operator_name=ticket.assigned_operator_name,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            allowed_transitions=[TransitionResponse.from_rule(rule) for rule in transitions],
        )


class HistoryEntryResponse(BaseModel):
    id: int
    ticket_id: int
    event_type: HistoryEventType
    from_status: TicketStatus | None
    to_status: TicketStatus | None
    comment: str | None
    actor: str
    created_at: datetime

    @classmethod
    def from_domain(cls, entry: HistoryEntry) -> "HistoryEntryResponse":
        return cls(**entry.__dict__)


class TicketDetailResponse(TicketResponse):
    history: list[HistoryEntryResponse]


class OperatorResponse(BaseModel):
    id: int
    full_name: str
    email: str

    @classmethod
    def from_domain(cls, operator: Operator) -> "OperatorResponse":
        return cls(**operator.__dict__)


class NotificationResponse(BaseModel):
    id: int
    ticket_id: int
    recipient: str
    channel: str
    message: str
    created_at: datetime

    @classmethod
    def from_domain(cls, notification: Notification) -> "NotificationResponse":
        return cls(**notification.__dict__)


class WorkflowResponse(BaseModel):
    statuses: list[TicketStatus]
    transitions: list[TransitionResponse]
