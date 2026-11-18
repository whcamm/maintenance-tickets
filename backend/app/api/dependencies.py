from typing import Annotated

import pymysql
from fastapi import Depends

from app.core.config import get_settings
from app.core.database import get_connection
from app.domain.workflow import TicketWorkflow
from app.repositories.notification_repository import MySqlNotificationRepository
from app.repositories.operator_repository import MySqlOperatorRepository
from app.repositories.ticket_repository import MySqlTicketRepository
from app.services.notification_service import NotificationService
from app.services.ticket_service import TicketService

Connection = Annotated[pymysql.connections.Connection, Depends(get_connection)]


def get_workflow() -> TicketWorkflow:
    return TicketWorkflow()


def get_notification_service(connection: Connection) -> NotificationService:
    return NotificationService(
        notifications=MySqlNotificationRepository(connection),
        operators=MySqlOperatorRepository(connection),
        maintenance_team_email=get_settings().maintenance_team_email,
    )


def get_ticket_service(
    connection: Connection,
    notifications: Annotated[NotificationService, Depends(get_notification_service)],
    workflow: Annotated[TicketWorkflow, Depends(get_workflow)],
) -> TicketService:
    return TicketService(
        tickets=MySqlTicketRepository(connection),
        operators=MySqlOperatorRepository(connection),
        notifications=notifications,
        workflow=workflow,
    )


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
WorkflowDep = Annotated[TicketWorkflow, Depends(get_workflow)]
