from typing import Annotated

from fastapi import APIRouter, Query

from app.api.dependencies import Connection, NotificationServiceDep, TicketServiceDep, WorkflowDep
from app.api.schemas import NotificationResponse, OperatorResponse, TransitionResponse, WorkflowResponse
from app.domain.workflow import TicketStatus

router = APIRouter()


@router.get("/health", tags=["Health"], summary="Check API and database availability")
def health(connection: Connection) -> dict[str, str]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return {"status": "ok"}


@router.get("/workflow", response_model=WorkflowResponse, tags=["Workflow"], summary="Get the ticket state machine")
def get_workflow(workflow: WorkflowDep) -> WorkflowResponse:
    return WorkflowResponse(
        statuses=list(TicketStatus),
        transitions=[TransitionResponse.from_rule(rule) for rule in workflow.rules],
    )


@router.get("/operators", response_model=list[OperatorResponse], tags=["Operators"], summary="List operators")
def list_operators(service: TicketServiceDep) -> list[OperatorResponse]:
    return [OperatorResponse.from_domain(operator) for operator in service.list_operators()]


@router.get(
    "/notifications",
    response_model=list[NotificationResponse],
    tags=["Notifications"],
    summary="List the latest simulated notifications",
)
def list_notifications(
    service: NotificationServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[NotificationResponse]:
    return [NotificationResponse.from_domain(notification) for notification in service.recent(limit)]
