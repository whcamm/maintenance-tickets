from dataclasses import dataclass
from enum import StrEnum

from app.domain.exceptions import BusinessRuleViolationError, InvalidTransitionError


class TicketStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class TransitionRule:
    source: TicketStatus
    target: TicketStatus
    requires_diagnosis: bool = False
    requires_comment: bool = False


TRANSITION_RULES: tuple[TransitionRule, ...] = (
    TransitionRule(TicketStatus.PENDING, TicketStatus.IN_PROGRESS),
    TransitionRule(TicketStatus.PENDING, TicketStatus.RESOLVED, requires_diagnosis=True),
    TransitionRule(TicketStatus.IN_PROGRESS, TicketStatus.PENDING, requires_comment=True),
    TransitionRule(TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, requires_diagnosis=True),
    TransitionRule(TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS, requires_comment=True),
    TransitionRule(TicketStatus.RESOLVED, TicketStatus.CLOSED),
)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


class TicketWorkflow:
    def __init__(self, rules: tuple[TransitionRule, ...] = TRANSITION_RULES) -> None:
        self._rules = {(rule.source, rule.target): rule for rule in rules}

    @property
    def rules(self) -> list[TransitionRule]:
        return list(self._rules.values())

    def allowed_transitions(self, source: TicketStatus) -> list[TransitionRule]:
        return [rule for rule in self._rules.values() if rule.source == source]

    def validate(
        self,
        source: TicketStatus,
        target: TicketStatus,
        diagnosis: str | None = None,
        comment: str | None = None,
    ) -> TransitionRule:
        if source == target:
            raise InvalidTransitionError(f"Ticket is already in status {source}.")

        rule = self._rules.get((source, target))
        if rule is None:
            raise InvalidTransitionError(f"Transition from {source} to {target} is not allowed.")

        if rule.requires_diagnosis and not _has_text(diagnosis):
            raise BusinessRuleViolationError(
                f"A diagnosis is required to move a ticket from {source} to {target}."
            )

        if rule.requires_comment and not _has_text(comment):
            raise BusinessRuleViolationError(
                f"A comment is required to move a ticket from {source} to {target}."
            )

        return rule
