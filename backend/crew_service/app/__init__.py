# app/__init__.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

from app.api.crew_endpoints import crew_router
from app.api.schemas_endpoints import schemas_router
from app.api.status_endpoints import status_router
from app.api.tasks_endpoints import tasks_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def init_routers(app: FastAPI) -> None:
    """Register all API routers."""
    app.include_router(status_router)
    app.include_router(crew_router)
    app.include_router(tasks_router)
    app.include_router(schemas_router)


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_routers(app)
    return app


app = create_app()
