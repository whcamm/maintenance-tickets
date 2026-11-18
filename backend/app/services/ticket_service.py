from app.domain.exceptions import NotFoundError
from app.domain.models import HistoryEntry, NewTicket, Operator, Ticket, TicketFilters
from app.domain.ports import OperatorRepository, TicketRepository
from app.domain.workflow import TicketStatus, TicketWorkflow, TransitionRule
from app.services.notification_service import NotificationService


class TicketService:
    def __init__(
        self,
        tickets: TicketRepository,
        operators: OperatorRepository,
        notifications: NotificationService,
        workflow: TicketWorkflow,
    ) -> None:
        self._tickets = tickets
        self._operators = operators
        self._notifications = notifications
        self._workflow = workflow

    def create_ticket(self, new_ticket: NewTicket) -> Ticket:
        if new_ticket.assigned_operator_id is not None:
            self._get_operator(new_ticket.assigned_operator_id)
        ticket_id = self._tickets.create(new_ticket)
        return self.get_ticket(ticket_id)

    def get_ticket(self, ticket_id: int) -> Ticket:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket #{ticket_id} was not found.")
        return ticket

    def list_tickets(self, filters: TicketFilters) -> list[Ticket]:
        return self._tickets.search(filters)

    def get_history(self, ticket_id: int) -> list[HistoryEntry]:
        self.get_ticket(ticket_id)
        return self._tickets.history(ticket_id)

    def allowed_transitions(self, ticket: Ticket) -> list[TransitionRule]:
        return self._workflow.allowed_transitions(ticket.status)

    def change_status(
        self,
        ticket_id: int,
        target: TicketStatus,
        actor: str,
        diagnosis: str | None = None,
        comment: str | None = None,
    ) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        self._workflow.validate(
            ticket.status,
            target,
            diagnosis=diagnosis or ticket.diagnosis,
            comment=comment,
        )
        history_id = self._tickets.transition(ticket_id, target, diagnosis, comment, actor)
        updated_ticket = self.get_ticket(ticket_id)
        self._notifications.notify_status_change(updated_ticket, ticket.status, history_id)
        return updated_ticket

    def add_comment(self, ticket_id: int, comment: str, actor: str) -> HistoryEntry:
        self.get_ticket(ticket_id)
        history_id = self._tickets.add_comment(ticket_id, comment, actor)
        entry = self._tickets.history_entry(history_id)
        if entry is None:
            raise NotFoundError(f"History entry #{history_id} was not found.")
        return entry

    def assign_ticket(self, ticket_id: int, operator_id: int, actor: str) -> Ticket:
        self.get_ticket(ticket_id)
        operator = self._get_operator(operator_id)
        history_id = self._tickets.assign(ticket_id, operator_id, actor)
        updated_ticket = self.get_ticket(ticket_id)
        self._notifications.notify_assignment(updated_ticket, operator, history_id)
        return updated_ticket

    def list_operators(self) -> list[Operator]:
        return self._operators.find_all()

    def _get_operator(self, operator_id: int) -> Operator:
        operator = self._operators.get(operator_id)
        if operator is None:
            raise NotFoundError(f"Operator #{operator_id} was not found.")
        return operator
