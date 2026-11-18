from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.dependencies import TicketServiceDep
from app.api.schemas import (
    AssignmentRequest,
    CommentCreateRequest,
    HistoryEntryResponse,
    StatusTransitionRequest,
    TicketCreateRequest,
    TicketDetailResponse,
    TicketResponse,
)
from app.domain.exceptions import BusinessRuleViolationError
from app.domain.models import NewTicket, Ticket, TicketFilters
from app.domain.workflow import TicketStatus
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def to_response(service: TicketService, ticket: Ticket) -> TicketResponse:
    return TicketResponse.from_domain(ticket, service.allowed_transitions(ticket))


@router.get("", response_model=list[TicketResponse], summary="List tickets with optional filters")
def list_tickets(
    service: TicketServiceDep,
    ticket_status: Annotated[TicketStatus | None, Query(alias="status")] = None,
    operator_id: Annotated[int | None, Query(gt=0)] = None,
    created_from: Annotated[date | None, Query()] = None,
    created_to: Annotated[date | None, Query()] = None,
) -> list[TicketResponse]:
    if created_from and created_to and created_from > created_to:
        raise BusinessRuleViolationError("created_from must be earlier than or equal to created_to.")
    filters = TicketFilters(
        status=ticket_status,
        operator_id=operator_id,
        created_from=created_from,
        created_to=created_to,
    )
    return [to_response(service, ticket) for ticket in service.list_tickets(filters)]


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a new maintenance ticket",
)
def create_ticket(payload: TicketCreateRequest, service: TicketServiceDep) -> TicketResponse:
    ticket = service.create_ticket(
        NewTicket(
            title=payload.title,
            asset_code=payload.asset_code.upper(),
            description=payload.description or None,
            reported_by=payload.reported_by,
            assigned_operator_id=payload.assigned_operator_id,
        )
    )
    return to_response(service, ticket)


@router.get("/{ticket_id}", response_model=TicketDetailResponse, summary="Get a ticket with its history")
def get_ticket(ticket_id: int, service: TicketServiceDep) -> TicketDetailResponse:
    ticket = service.get_ticket(ticket_id)
    history = service.get_history(ticket_id)
    return TicketDetailResponse(
        **to_response(service, ticket).model_dump(),
        history=[HistoryEntryResponse.from_domain(entry) for entry in history],
    )


@router.get("/{ticket_id}/history", response_model=list[HistoryEntryResponse], summary="Get ticket history")
def get_history(ticket_id: int, service: TicketServiceDep) -> list[HistoryEntryResponse]:
    return [HistoryEntryResponse.from_domain(entry) for entry in service.get_history(ticket_id)]


@router.post(
    "/{ticket_id}/transitions",
    response_model=TicketResponse,
    summary="Move a ticket to another status",
    responses={409: {"description": "Transition not allowed"}, 422: {"description": "Business rule violated"}},
)
def change_status(ticket_id: int, payload: StatusTransitionRequest, service: TicketServiceDep) -> TicketResponse:
    ticket = service.change_status(
        ticket_id,
        payload.to_status,
        actor=payload.actor,
        diagnosis=payload.diagnosis or None,
        comment=payload.comment or None,
    )
    return to_response(service, ticket)


@router.post(
    "/{ticket_id}/comments",
    response_model=HistoryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to the ticket history",
)
def add_comment(ticket_id: int, payload: CommentCreateRequest, service: TicketServiceDep) -> HistoryEntryResponse:
    entry = service.add_comment(ticket_id, payload.comment, payload.actor)
    return HistoryEntryResponse.from_domain(entry)


@router.put("/{ticket_id}/assignment", response_model=TicketResponse, summary="Assign a ticket to an operator")
def assign_ticket(ticket_id: int, payload: AssignmentRequest, service: TicketServiceDep) -> TicketResponse:
    ticket = service.assign_ticket(ticket_id, payload.operator_id, payload.actor)
    return to_response(service, ticket)
