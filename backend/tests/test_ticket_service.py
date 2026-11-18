import pytest

from app.domain.exceptions import BusinessRuleViolationError, InvalidTransitionError, NotFoundError
from app.domain.models import HistoryEventType, NewTicket
from app.domain.workflow import TicketStatus
from tests.fakes import InMemoryContext


@pytest.fixture
def context() -> InMemoryContext:
    return InMemoryContext()


def create_ticket(context: InMemoryContext, operator_id: int | None = None):
    return context.service.create_ticket(
        NewTicket(
            title="ATM out of service",
            asset_code="ATM-0451",
            description="Screen does not respond.",
            reported_by="Branch manager",
            assigned_operator_id=operator_id,
        )
    )


def test_new_ticket_starts_pending_with_created_event(context):
    ticket = create_ticket(context)

    history = context.service.get_history(ticket.id)
    assert ticket.status == TicketStatus.PENDING
    assert [entry.event_type for entry in history] == [HistoryEventType.CREATED]


def test_full_lifecycle_is_recorded_in_history(context):
    ticket = create_ticket(context, operator_id=1)

    context.service.change_status(ticket.id, TicketStatus.IN_PROGRESS, actor="Andrea Rojas")
    context.service.change_status(ticket.id, TicketStatus.RESOLVED, actor="Andrea Rojas", diagnosis="Power supply replaced")
    closed = context.service.change_status(ticket.id, TicketStatus.CLOSED, actor="Andrea Rojas")

    transitions = [
        (entry.from_status, entry.to_status)
        for entry in context.service.get_history(ticket.id)
        if entry.event_type == HistoryEventType.STATUS_CHANGED
    ]
    assert closed.status == TicketStatus.CLOSED
    assert closed.diagnosis == "Power supply replaced"
    assert transitions == [
        (TicketStatus.PENDING, TicketStatus.IN_PROGRESS),
        (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED),
        (TicketStatus.RESOLVED, TicketStatus.CLOSED),
    ]


def test_resolving_without_diagnosis_is_blocked_and_not_persisted(context):
    ticket = create_ticket(context)

    with pytest.raises(BusinessRuleViolationError):
        context.service.change_status(ticket.id, TicketStatus.RESOLVED, actor="Operator")

    assert context.service.get_ticket(ticket.id).status == TicketStatus.PENDING
    assert len(context.service.get_history(ticket.id)) == 1


def test_invalid_transition_is_blocked(context):
    ticket = create_ticket(context)

    with pytest.raises(InvalidTransitionError):
        context.service.change_status(ticket.id, TicketStatus.CLOSED, actor="Operator")


def test_existing_diagnosis_allows_resolving_again(context):
    ticket = create_ticket(context)
    context.service.change_status(ticket.id, TicketStatus.RESOLVED, actor="Operator", diagnosis="Loose cable")
    context.service.change_status(ticket.id, TicketStatus.IN_PROGRESS, actor="Operator", comment="Failure repeated")

    resolved = context.service.change_status(ticket.id, TicketStatus.RESOLVED, actor="Operator")

    assert resolved.status == TicketStatus.RESOLVED
    assert resolved.diagnosis == "Loose cable"


def test_status_change_sends_notification_to_assigned_operator(context):
    ticket = create_ticket(context, operator_id=2)

    context.service.change_status(ticket.id, TicketStatus.IN_PROGRESS, actor="Luis Paredes")

    notification = context.notification_repository.notifications[-1]
    assert notification.recipient == "luis@test.local"
    assert "PENDING to IN_PROGRESS" in notification.message


def test_unassigned_ticket_notifies_maintenance_team(context):
    ticket = create_ticket(context)

    context.service.change_status(ticket.id, TicketStatus.IN_PROGRESS, actor="Operator")

    assert context.notification_repository.notifications[-1].recipient == "team@test.local"


def test_assignment_updates_ticket_and_history(context):
    ticket = create_ticket(context)

    assigned = context.service.assign_ticket(ticket.id, operator_id=1, actor="Supervisor")

    assert assigned.assigned_operator_name == "Andrea Rojas"
    assert context.service.get_history(ticket.id)[-1].event_type == HistoryEventType.ASSIGNED


def test_unknown_ticket_and_operator_raise_not_found(context):
    ticket = create_ticket(context)

    with pytest.raises(NotFoundError):
        context.service.get_ticket(9999)
    with pytest.raises(NotFoundError):
        context.service.assign_ticket(ticket.id, operator_id=99, actor="Supervisor")


def test_comment_is_added_to_history(context):
    ticket = create_ticket(context)

    entry = context.service.add_comment(ticket.id, "Technician on the way", actor="Operator")

    assert entry.event_type == HistoryEventType.COMMENT
    assert entry.comment == "Technician on the way"
