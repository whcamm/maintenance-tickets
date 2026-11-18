import logging

from app.domain.models import Notification, Operator, Ticket
from app.domain.ports import NotificationRepository, OperatorRepository
from app.domain.workflow import TicketStatus

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        notifications: NotificationRepository,
        operators: OperatorRepository,
        maintenance_team_email: str,
    ) -> None:
        self._notifications = notifications
        self._operators = operators
        self._maintenance_team_email = maintenance_team_email

    def notify_status_change(self, ticket: Ticket, previous_status: TicketStatus, history_id: int) -> None:
        message = f"Ticket #{ticket.id} ({ticket.asset_code}) moved from {previous_status} to {ticket.status}."
        self._send(ticket.id, history_id, self._recipient_for(ticket), message)

    def notify_assignment(self, ticket: Ticket, operator: Operator, history_id: int) -> None:
        message = f"Ticket #{ticket.id} ({ticket.asset_code}) was assigned to you."
        self._send(ticket.id, history_id, operator.email, message)

    def recent(self, limit: int = 20) -> list[Notification]:
        return self._notifications.recent(limit)

    def _recipient_for(self, ticket: Ticket) -> str:
        if ticket.assigned_operator_id is not None:
            operator = self._operators.get(ticket.assigned_operator_id)
            if operator is not None:
                return operator.email
        return self._maintenance_team_email

    def _send(self, ticket_id: int, history_id: int, recipient: str, message: str) -> None:
        try:
            self._notifications.save(ticket_id, history_id, recipient, message)
            logger.info("Simulated email to %s: %s", recipient, message)
        except Exception:
            logger.exception("Notification for ticket %s could not be stored", ticket_id)
