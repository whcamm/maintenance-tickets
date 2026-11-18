from datetime import UTC, datetime, timedelta
from itertools import count

from app.domain.models import (
    HistoryEntry,
    HistoryEventType,
    NewTicket,
    Notification,
    Operator,
    Ticket,
    TicketFilters,
)
from app.domain.workflow import TicketStatus, TicketWorkflow
from app.services.notification_service import NotificationService
from app.services.ticket_service import TicketService


class InMemoryOperatorRepository:
    def __init__(self) -> None:
        self.operators = {
            1: Operator(id=1, full_name="Andrea Rojas", email="andrea@test.local"),
            2: Operator(id=2, full_name="Luis Paredes", email="luis@test.local"),
        }

    def find_all(self) -> list[Operator]:
        return list(self.operators.values())

    def get(self, operator_id: int) -> Operator | None:
        return self.operators.get(operator_id)


class InMemoryTicketRepository:
    def __init__(self, operators: InMemoryOperatorRepository) -> None:
        self._operators = operators
        self._ticket_ids = count(1000)
        self._history_ids = count(1)
        self.tickets: dict[int, Ticket] = {}
        self.entries: list[HistoryEntry] = []

    def create(self, new_ticket: NewTicket) -> int:
        ticket_id = next(self._ticket_ids)
        now = datetime.now(UTC)
        operator = self._operators.get(new_ticket.assigned_operator_id) if new_ticket.assigned_operator_id else None
        self.tickets[ticket_id] = Ticket(
            id=ticket_id,
            title=new_ticket.title,
            asset_code=new_ticket.asset_code,
            description=new_ticket.description,
            status=TicketStatus.PENDING,
            diagnosis=None,
            reported_by=new_ticket.reported_by,
            assigned_operator_id=operator.id if operator else None,
            assigned_operator_name=operator.full_name if operator else None,
            created_at=now,
            updated_at=now,
        )
        self._record(ticket_id, HistoryEventType.CREATED, None, TicketStatus.PENDING, None, new_ticket.reported_by)
        return ticket_id

    def get(self, ticket_id: int) -> Ticket | None:
        return self.tickets.get(ticket_id)

    def search(self, filters: TicketFilters) -> list[Ticket]:
        tickets = list(self.tickets.values())
        if filters.status:
            tickets = [ticket for ticket in tickets if ticket.status == filters.status]
        if filters.operator_id:
            tickets = [ticket for ticket in tickets if ticket.assigned_operator_id == filters.operator_id]
        if filters.created_from:
            tickets = [ticket for ticket in tickets if ticket.created_at.date() >= filters.created_from]
        if filters.created_to:
            limit = filters.created_to + timedelta(days=1)
            tickets = [ticket for ticket in tickets if ticket.created_at.date() < limit]
        return tickets

    def transition(self, ticket_id, target, diagnosis, comment, actor) -> int:
        ticket = self.tickets[ticket_id]
        self.tickets[ticket_id] = self._replace(ticket, status=target, diagnosis=diagnosis or ticket.diagnosis)
        return self._record(ticket_id, HistoryEventType.STATUS_CHANGED, ticket.status, target, comment, actor)

    def add_comment(self, ticket_id: int, comment: str, actor: str) -> int:
        return self._record(ticket_id, HistoryEventType.COMMENT, None, None, comment, actor)

    def assign(self, ticket_id: int, operator_id: int, actor: str) -> int:
        operator = self._operators.get(operator_id)
        ticket = self.tickets[ticket_id]
        self.tickets[ticket_id] = self._replace(
            ticket, assigned_operator_id=operator.id, assigned_operator_name=operator.full_name
        )
        return self._record(ticket_id, HistoryEventType.ASSIGNED, None, None, f"Assigned to {operator.full_name}.", actor)

    def history(self, ticket_id: int) -> list[HistoryEntry]:
        return [entry for entry in self.entries if entry.ticket_id == ticket_id]

    def history_entry(self, history_id: int) -> HistoryEntry | None:
        return next((entry for entry in self.entries if entry.id == history_id), None)

    def _record(self, ticket_id, event_type, from_status, to_status, comment, actor) -> int:
        history_id = next(self._history_ids)
        self.entries.append(
            HistoryEntry(
                id=history_id,
                ticket_id=ticket_id,
                event_type=event_type,
                from_status=from_status,
                to_status=to_status,
                comment=comment,
                actor=actor,
                created_at=datetime.now(UTC),
            )
        )
        return history_id

    @staticmethod
    def _replace(ticket: Ticket, **changes) -> Ticket:
        return Ticket(**{**ticket.__dict__, **changes, "updated_at": datetime.now(UTC)})


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self.notifications: list[Notification] = []

    def save(self, ticket_id: int, history_id: int, recipient: str, message: str) -> int:
        notification = Notification(
            id=len(self.notifications) + 1,
            ticket_id=ticket_id,
            recipient=recipient,
            channel="EMAIL_SIMULATED",
            message=message,
            created_at=datetime.now(UTC),
        )
        self.notifications.append(notification)
        return notification.id

    def recent(self, limit: int) -> list[Notification]:
        return list(reversed(self.notifications))[:limit]


class InMemoryContext:
    def __init__(self) -> None:
        self.operators = InMemoryOperatorRepository()
        self.tickets = InMemoryTicketRepository(self.operators)
        self.notification_repository = InMemoryNotificationRepository()
        self.notifications = NotificationService(
            self.notification_repository, self.operators, maintenance_team_email="team@test.local"
        )
        self.service = TicketService(self.tickets, self.operators, self.notifications, TicketWorkflow())
