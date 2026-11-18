import re
from pathlib import Path

import pytest

from app.domain.exceptions import BusinessRuleViolationError, InvalidTransitionError
from app.domain.workflow import TRANSITION_RULES, TicketStatus, TicketWorkflow

SEED_SCRIPT = Path(__file__).resolve().parents[2] / "db" / "03_seed.sql"

workflow = TicketWorkflow()


@pytest.mark.parametrize(
    ("source", "target", "diagnosis", "comment"),
    [
        (TicketStatus.PENDING, TicketStatus.IN_PROGRESS, None, None),
        (TicketStatus.PENDING, TicketStatus.RESOLVED, "Fuse replaced", None),
        (TicketStatus.IN_PROGRESS, TicketStatus.PENDING, None, "Waiting for spare parts"),
        (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, "Cable reconnected", None),
        (TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS, None, "Issue came back"),
        (TicketStatus.RESOLVED, TicketStatus.CLOSED, None, None),
    ],
)
def test_valid_transitions_are_accepted(source, target, diagnosis, comment):
    rule = workflow.validate(source, target, diagnosis=diagnosis, comment=comment)

    assert rule.source == source
    assert rule.target == target


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (TicketStatus.PENDING, TicketStatus.CLOSED),
        (TicketStatus.IN_PROGRESS, TicketStatus.CLOSED),
        (TicketStatus.RESOLVED, TicketStatus.PENDING),
        (TicketStatus.CLOSED, TicketStatus.IN_PROGRESS),
        (TicketStatus.CLOSED, TicketStatus.PENDING),
        (TicketStatus.PENDING, TicketStatus.PENDING),
    ],
)
def test_invalid_transitions_are_rejected(source, target):
    with pytest.raises(InvalidTransitionError):
        workflow.validate(source, target, diagnosis="any", comment="any")


@pytest.mark.parametrize("diagnosis", [None, "", "   "])
def test_pending_to_resolved_requires_diagnosis(diagnosis):
    with pytest.raises(BusinessRuleViolationError, match="diagnosis"):
        workflow.validate(TicketStatus.PENDING, TicketStatus.RESOLVED, diagnosis=diagnosis)


def test_reopening_requires_comment():
    with pytest.raises(BusinessRuleViolationError, match="comment"):
        workflow.validate(TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS)


def test_closed_is_a_final_state():
    assert workflow.allowed_transitions(TicketStatus.CLOSED) == []


def test_database_seed_matches_domain_rules():
    seed = SEED_SCRIPT.read_text(encoding="utf-8")
    rows = re.findall(r"\('(\w+)', '(\w+)', (TRUE|FALSE), (TRUE|FALSE)\)", seed)
    seeded = {(source, target, diagnosis == "TRUE", comment == "TRUE") for source, target, diagnosis, comment in rows}
    expected = {
        (rule.source.value, rule.target.value, rule.requires_diagnosis, rule.requires_comment)
        for rule in TRANSITION_RULES
    }

    assert seeded == expected
