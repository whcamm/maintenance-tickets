from typing import Protocol

from app.domain.models import HistoryEntry, NewTicket, Notification, Operator, Ticket, TicketFilters
from app.domain.workflow import TicketStatus


class TicketRepository(Protocol):
    def create(self, new_ticket: NewTicket) -> int: ...

    def get(self, ticket_id: int) -> Ticket | None: ...

    def search(self, filters: TicketFilters) -> list[Ticket]: ...

    def transition(
        self,
        ticket_id: int,
        target: TicketStatus,
        diagnosis: str | None,
        comment: str | None,
        actor: str,
    ) -> int: ...

    def add_comment(self, ticket_id: int, comment: str, actor: str) -> int: ...

    def assign(self, ticket_id: int, operator_id: int, actor: str) -> int: ...

    def history(self, ticket_id: int) -> list[HistoryEntry]: ...

    def history_entry(self, history_id: int) -> HistoryEntry | None: ...


class OperatorRepository(Protocol):
    def find_all(self) -> list[Operator]: ...

    def get(self, operator_id: int) -> Operator | None: ...


class NotificationRepository(Protocol):
    def save(self, ticket_id: int, history_id: int, recipient: str, message: str) -> int: ...

    def recent(self, limit: int) -> list[Notification]: ...
