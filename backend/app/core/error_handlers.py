import logging

import pymysql
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    InvalidTransitionError,
    NotFoundError,
)

logger = logging.getLogger(__name__)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidTransitionError: status.HTTP_409_CONFLICT,
    ConflictError: status.HTTP_409_CONFLICT,
    BusinessRuleViolationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def error_body(code: str, message: str, details: list[dict] | None = None) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        status_code = STATUS_BY_ERROR.get(type(exc), status.HTTP_400_BAD_REQUEST)
        return JSONResponse(status_code=status_code, content=error_body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=error_body("VALIDATION_ERROR", "The request contains invalid data.", details),
        )

    @app.exception_handler(pymysql.err.OperationalError)
    async def handle_database_unavailable(_: Request, exc: pymysql.err.OperationalError) -> JSONResponse:
        logger.error("Database operational error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_body("DATABASE_UNAVAILABLE", "The database is temporarily unavailable."),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_body("INTERNAL_ERROR", "An unexpected error occurred. Please try again later."),
        )
