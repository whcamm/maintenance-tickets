import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import catalog, tickets
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Maintenance Tickets API",
        version="1.0.0",
        description="Maintenance ticket workflow with a state machine and a persisted event history.",
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PUT"],
            allow_headers=["Content-Type"],
        )

    register_error_handlers(app)
    app.include_router(catalog.router, prefix="/api")
    app.include_router(tickets.router, prefix="/api")

    if settings.frontend_dist_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_dist_dir, html=True), name="frontend")

    return app


app = create_app()
